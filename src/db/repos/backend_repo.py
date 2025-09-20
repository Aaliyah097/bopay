from aiohttp import ClientSession
from src.settings import settings


async def unlock_candidate(session: ClientSession, candidate_id: str | int):
    response = await session.post(
        settings.BACKEND_UNLOCK_CANDIDATE_URL % str(candidate_id),
        headers={'x-api-key': settings.BACKEND_API_KEY}
    )
    if response.status != 200:
        response.raise_for_status()


async def destroy_candidate(session: ClientSession, candidate_id: str | int):
    response = await session.delete(
        settings.BACKEND_DESTROY_CANDIDATE_URL % str(candidate_id),
        headers={'x-api-key': settings.BACKEND_API_KEY}
    )
    if response.status not in [204, 404]:
        response.raise_for_status()
