import asyncio
from app.database import AsyncSessionLocal, engine, Base
from app.models import User, Corner, CheckIn, Route, RouteCorner, Achievement
from app.auth import get_password_hash


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        hashed_pw = get_password_hash("123456")

        user1 = User(
            username="explorer1",
            email="explorer1@example.com",
            hashed_password=hashed_pw,
            avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=explorer1",
            bio="热爱探索城市的每一个角落"
        )
        user2 = User(
            username="traveler2",
            email="traveler2@example.com",
            hashed_password=hashed_pw,
            avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=traveler2",
            bio="用脚步丈量城市的温度"
        )
        db.add_all([user1, user2])
        await db.flush()

        corners = [
            Corner(
                title="老巷子里的百年茶馆",
                description="隐藏在繁华商业街背后的一条老巷子里，有一家经营了百年的老茶馆。这里保留着最传统的泡茶技艺，茶香四溢，时光仿佛在这里静止。",
                category="人文古迹",
                latitude=39.9042,
                longitude=116.4074,
                address="北京市东城区老茶巷18号",
                images="https://images.unsplash.com/photo-1564890369478-c89ca6d9cde9?w=800",
                tags="茶馆,老北京,怀旧,传统文化",
                difficulty="easy",
                author_id=user1.id
            ),
            Corner(
                title="城市天台秘密花园",
                description="在一栋老式居民楼的天台上，有一位老人精心打造了一片秘密花园。各种花卉四季盛开，是俯瞰城市天际线的绝佳地点。",
                category="自然风光",
                latitude=39.9142,
                longitude=116.4174,
                address="北京市西城区花园路5号楼天台",
                images="https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=800",
                tags="天台,花园,摄影,城市景观",
                difficulty="medium",
                author_id=user1.id
            ),
            Corner(
                title="24小时不打烊书店",
                description="这家深夜书店为城市的夜猫子们提供了一个温暖的港湾。店内有舒适的阅读角落，每晚还有读书分享会。",
                category="文艺空间",
                latitude=39.9242,
                longitude=116.4274,
                address="北京市朝阳区文化路88号",
                images="https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?w=800",
                tags="书店,24小时,阅读,文艺",
                difficulty="easy",
                author_id=user2.id
            ),
            Corner(
                title="废弃铁轨艺术区",
                description="一段被遗忘的城市铁轨，被艺术家们改造成了露天艺术展区。铁轨两侧布满了涂鸦和雕塑作品，非常适合拍照。",
                category="艺术创意",
                latitude=39.9342,
                longitude=116.4374,
                address="北京市海淀区艺术区西段",
                images="https://images.unsplash.com/photo-1518998053901-5348d3961a04?w=800",
                tags="涂鸦,艺术,铁轨,摄影",
                difficulty="medium",
                author_id=user2.id
            ),
            Corner(
                title="胡同里的手作工坊",
                description="在一条安静的胡同里，有一家小小的皮具手作工坊。主人是一位老匠人，可以在这里学习传统皮具制作技艺。",
                category="体验工坊",
                latitude=39.9442,
                longitude=116.4474,
                address="北京市东城区匠人胡同3号",
                images="https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800",
                tags="手作,皮具,体验,非遗",
                difficulty="easy",
                author_id=user1.id
            ),
            Corner(
                title="城市湿地公园",
                description="在市中心有一片难得的湿地公园，是城市的绿肺。这里栖息着多种鸟类，清晨和傍晚时分最美。",
                category="自然风光",
                latitude=39.9542,
                longitude=116.4574,
                address="北京市丰台区湿地公园",
                images="https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800",
                tags="湿地,自然,观鸟,散步",
                difficulty="easy",
                author_id=user2.id
            ),
            Corner(
                title="老钟表修理铺",
                description="一家开了60年的老钟表修理铺，主人是一位70多岁的老师傅。店里挂满了各式各样的老钟表，滴滴答答的声音仿佛在诉说时光的故事。",
                category="人文古迹",
                latitude=39.9642,
                longitude=116.4674,
                address="北京市西城区钟表胡同12号",
                images="https://images.unsplash.com/photo-1509048191080-d2984bad6ae5?w=800",
                tags="钟表,怀旧,老手艺,复古",
                difficulty="hard",
                author_id=user1.id
            ),
            Corner(
                title="屋顶咖啡书屋",
                description="隐藏在老建筑屋顶的咖啡书屋，可以一边品尝手冲咖啡，一边阅读好书，还能远眺城市风光。",
                category="文艺空间",
                latitude=39.9742,
                longitude=116.4774,
                address="北京市东城区书屋街6层",
                images="https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800",
                tags="咖啡,书屋,屋顶,休闲",
                difficulty="medium",
                author_id=user2.id
            )
        ]
        db.add_all(corners)
        await db.flush()

        checkins = [
            CheckIn(user_id=user2.id, corner_id=corners[0].id, content="终于找到这家老茶馆了，茶香真的很纯正！", rating=5),
            CheckIn(user_id=user2.id, corner_id=corners[1].id, content="天台花园太美了，拍了好多照片", rating=5),
            CheckIn(user_id=user1.id, corner_id=corners[2].id, content="深夜在这里看书感觉很安静", rating=4),
            CheckIn(user_id=user2.id, corner_id=corners[4].id, content="跟着老师傅做了一个小钱包，很有意义", rating=5),
        ]
        db.add_all(checkins)

        route1 = Route(
            user_id=user1.id,
            title="老北京文化一日游",
            description="探索北京最具代表性的人文角落，感受传统文化的魅力",
            estimated_time=480,
            distance=15.5
        )
        db.add(route1)
        await db.flush()

        route_corners = [
            RouteCorner(route_id=route1.id, corner_id=corners[0].id, order=0),
            RouteCorner(route_id=route1.id, corner_id=corners[4].id, order=1),
            RouteCorner(route_id=route1.id, corner_id=corners[6].id, order=2),
        ]
        db.add_all(route_corners)

        achievements = [
            Achievement(name="初出茅庐", description="完成第一次打卡", icon="🌱", condition_type="checkins", condition_value=1),
            Achievement(name="探索新手", description="完成5次打卡", icon="👣", condition_type="checkins", condition_value=5),
            Achievement(name="角落发现者", description="发布第一个角落", icon="🔍", condition_type="corners", condition_value=1),
            Achievement(name="路线规划师", description="创建第一条路线", icon="🗺️", condition_type="routes", condition_value=1),
        ]
        db.add_all(achievements)

        await db.commit()
        print("数据库初始化完成！")
        print("测试账号: explorer1 / 123456, traveler2 / 123456")


if __name__ == "__main__":
    asyncio.run(init_db())
