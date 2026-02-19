import os
import asyncio
import json

# Simular entorno sin OpenAI
os.environ.pop('AZURE_OPENAI_KEY', None)
os.environ.pop('AZURE_OPENAI_ENDPOINT', None)

from shared.core.orchestrator import OpportunityOrchestrator

async def main():
    o = OpportunityOrchestrator()
    print('openai_enabled:', getattr(o, 'openai_enabled', None))
    res = await o.process_opportunity({'opportunityid': 'sim-1', 'name': 'Simulacion'})
    print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    asyncio.run(main())
