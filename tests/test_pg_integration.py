import pytest
from db import get_connection
from repositories.ads import AdRepository
from repositories.users import UserRepository
from repositories.moderation_results import ModerationResultRepository

@pytest.mark.integration
@pytest.mark.asyncio
async def test_pg_repositories():
    async with get_connection() as conn:
        ad_repo = AdRepository(conn)
        user_repo = UserRepository(conn)
        mod_repo = ModerationResultRepository(conn)
        
        user = await user_repo.create(is_verified_seller=False)
        assert user.id is not None
        
        ad = await ad_repo.create(
            seller_id=user.id,
            title="Ad Title",
            description="Ad Desc",
            category=1,
            images_qty=2
        )
        assert ad.id is not None
        
        mod_res = await mod_repo.create_pending(item_id=ad.id)
        assert mod_res.id is not None
        assert mod_res.status == "pending"
        
        await mod_repo.update_result(
            task_id=mod_res.id,
            status="completed",
            is_violation=False,
            probability=0.2,
            error_message=None
        )
        
        fetched_mod = await mod_repo.get(mod_res.id)
        assert fetched_mod.status == "completed"
        assert fetched_mod.probability == 0.2
        
        await ad_repo.close(ad.id)
        
        fetched_ad = await ad_repo.get(ad.id)
        assert fetched_ad is None
        
        await mod_repo.delete_by_item_id(ad.id)
        
        fetched_mod_deleted = await mod_repo.get(mod_res.id)
        assert fetched_mod_deleted is None
