import asyncio
import os
from elevenlabs.client import AsyncElevenLabs

async def main():
    token = os.getenv("ELEVENLABS_API_KEY", "sk_e3fdeee67386aaab9c68a8d3d524a94985cb08ce29ee10cc")
    client = AsyncElevenLabs(api_key=token)
    try:
        response = await client.voices.get_all()
        voices = response.voices
        for v in voices:
            labels = v.labels or {}
            print(f"Name: {v.name}, ID: {v.voice_id}, Labels: {labels}")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
