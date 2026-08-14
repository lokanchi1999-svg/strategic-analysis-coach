"""OpenAI-compatible transport with bounded retries and structured-output modes."""
from __future__ import annotations
import asyncio, json, time
from typing import Any
import httpx
from ..schemas.model import GatewayResponse, GatewayUsage, ModelCredentials, ModelProfile, StructuredOutputMode
from .base import GatewayError, ModelGateway

class OpenAICompatibleGateway(ModelGateway):
    MAX_TRANSPORT_RETRIES=1
    def __init__(self, profile:ModelProfile, credentials:ModelCredentials, transport:httpx.AsyncBaseTransport|None=None):
        self.profile,self.credentials,self.transport=profile,credentials,transport

    def _modes(self,response_schema):
        if not response_schema: return [None]
        configured=self.profile.structured_output_mode
        return [StructuredOutputMode.JSON_SCHEMA,StructuredOutputMode.JSON_OBJECT,StructuredOutputMode.PROMPT_ONLY] if configured==StructuredOutputMode.AUTO else [configured]

    def _body(self,model,messages,response_schema,mode):
        body={"model":model,"messages":messages,"temperature":self.profile.generation.temperature,"max_tokens":self.profile.generation.max_output_tokens}
        if mode==StructuredOutputMode.JSON_SCHEMA:
            body["response_format"]={"type":"json_schema","json_schema":{"name":"evaluation_result","strict":True,"schema":response_schema}}
        elif mode==StructuredOutputMode.JSON_OBJECT: body["response_format"]={"type":"json_object"}
        return body

    async def _post_with_retry(self,url,headers,body):
        timeout=httpx.Timeout(self.profile.generation.timeout_seconds)
        for attempt in range(self.MAX_TRANSPORT_RETRIES+1):
            try:
                async with httpx.AsyncClient(timeout=timeout,transport=self.transport) as client: response=await client.post(url,headers=headers,json=body)
                if response.status_code==429 or 500<=response.status_code<600:
                    if attempt<self.MAX_TRANSPORT_RETRIES: await asyncio.sleep(0.1*(attempt+1)); continue
                return response
            except (httpx.ReadTimeout,httpx.ConnectTimeout) as exc:
                if attempt<self.MAX_TRANSPORT_RETRIES: await asyncio.sleep(0.1*(attempt+1)); continue
                raise GatewayError("MODEL_TIMEOUT","Model request timed out") from exc
            except httpx.RequestError as exc: raise GatewayError("MODEL_PROVIDER_ERROR","Model endpoint is unreachable") from exc
        raise GatewayError("MODEL_PROVIDER_ERROR","Model request failed")

    @staticmethod
    def _parse_object(content:str):
        """Parse exactly one JSON object; never mine JSON from surrounding prose."""
        text=content.strip()
        if not (text.startswith("{") and text.endswith("}")): return None
        try: value=json.loads(text)
        except json.JSONDecodeError: return None
        return value if isinstance(value,dict) else None

    async def generate(self,*,role:str,messages:list[dict[str,str]],response_schema:dict[str,Any]|None=None)->GatewayResponse:
        key=self.credentials.api_key.get_secret_value() if self.credentials.api_key else ""
        if not key: raise GatewayError("MODEL_AUTHENTICATION_FAILED","An API key is required")
        model=self.profile.models.resolve(role); started=time.perf_counter(); url=f"{self.profile.base_url.rstrip('/')}/chat/completions"; headers={"Authorization":f"Bearer {key}"}
        last_unsupported=None
        for mode in self._modes(response_schema):
            body=self._body(model,messages,response_schema,mode); response=await self._post_with_retry(url,headers,body)
            if response.status_code in (401,403): raise GatewayError("MODEL_AUTHENTICATION_FAILED","Authentication failed")
            if response.status_code==404: raise GatewayError("MODEL_PROVIDER_ERROR","Endpoint or model was not found")
            if response.status_code in (400,422) and response_schema and self.profile.structured_output_mode==StructuredOutputMode.AUTO:
                last_unsupported=response.status_code; continue
            if response.status_code==429: raise GatewayError("MODEL_RATE_LIMITED","Model provider rate limit exceeded")
            if response.status_code>=400: raise GatewayError("MODEL_PROVIDER_ERROR",f"Provider request failed ({response.status_code})")
            try:
                payload=response.json(); content=payload["choices"][0]["message"]["content"]; usage=payload.get("usage",{})
            except (ValueError,KeyError,TypeError) as exc: raise GatewayError("MODEL_PROVIDER_ERROR","Provider returned an invalid response envelope") from exc
            self.last_structured_output_mode=mode
            return GatewayResponse(content=content,structured_output=self._parse_object(content) if response_schema else None,usage=GatewayUsage(input_tokens=usage.get("prompt_tokens"),output_tokens=usage.get("completion_tokens")),model=payload.get("model",model),latency_ms=(time.perf_counter()-started)*1000,structured_output_mode=mode)
        raise GatewayError("MODEL_PROVIDER_ERROR",f"Provider rejected all structured-output modes ({last_unsupported})")
