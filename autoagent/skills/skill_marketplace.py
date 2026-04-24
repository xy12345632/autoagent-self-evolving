"""
技能市场 - 类似 agentskills.io 的技能共享平台
"""

import json
import hashlib
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

from .skill_exporter import SkillImporter


@dataclass
class SkillListing:
    id: str
    name: str
    description: str
    category: str
    tags: List[str]
    author: str
    version: str
    rating: float
    download_count: int
    created_at: str
    updated_at: str
    skill_data: Dict[str, Any]
    manifest_path: Optional[str] = None


class SkillMarketplace:
    """
    本地技能市场

    功能:
    1. 发布技能到本地市场
    2. 浏览和搜索市场中的技能
    3. 安装市场中的技能
    4. 技能评分和统计
    """

    def __init__(self, marketplace_dir: Optional[str] = None):
        if marketplace_dir:
            self.marketplace_dir = Path(marketplace_dir)
        else:
            from ..utils.paths import GlobalPaths
            self.marketplace_dir = GlobalPaths.get_data_dir() / "skill_marketplace"

        self.marketplace_dir.mkdir(parents=True, exist_ok=True)
        self.listings_file = self.marketplace_dir / "listings.json"
        self._listings: Dict[str, SkillListing] = {}
        self._load_listings()

    def _load_listings(self) -> None:
        if self.listings_file.exists():
            try:
                with open(self.listings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for listing_data in data.values():
                        self._listings[listing_data['id']] = SkillListing(**listing_data)
            except Exception:
                self._listings = {}

    def _save_listings(self) -> None:
        data = {k: asdict(v) for k, v in self._listings.items()}
        with open(self.listings_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _generate_id(self, name: str, author: str) -> str:
        raw = f"{name}:{author}".encode('utf-8')
        return hashlib.md5(raw).hexdigest()[:12]

    def publish_skill(
        self,
        skill_data: Dict[str, Any],
        author: str = "local",
        version: str = "1.0.0"
    ) -> str:
        """
        发布技能到市场

        Args:
            skill_data: 技能数据
            author: 作者名
            version: 版本号

        Returns:
            listing_id: 技能列表ID
        """
        listing_id = self._generate_id(skill_data.get('name', ''), author)

        if listing_id in self._listings:
            existing = self._listings[listing_id]
            existing.version = version
            existing.updated_at = datetime.now().isoformat()
            existing.skill_data = skill_data
            self._save_listings()
            return listing_id

        listing = SkillListing(
            id=listing_id,
            name=skill_data.get('name', 'Unnamed'),
            description=skill_data.get('description', ''),
            category=skill_data.get('category', 'general'),
            tags=skill_data.get('tags', []),
            author=author,
            version=version,
            rating=0.0,
            download_count=0,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            skill_data=skill_data
        )

        self._listings[listing_id] = listing
        self._save_listings()

        manifest_path = self.marketplace_dir / f"{listing_id}.skill.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(skill_data, f, ensure_ascii=False, indent=2)
        listing.manifest_path = str(manifest_path)

        self._save_listings()
        return listing_id

    def browse(
        self,
        category: Optional[str] = None,
        sort_by: str = "rating",
        limit: int = 20
    ) -> List[SkillListing]:
        """
        浏览市场中的技能

        Args:
            category: 按分类筛选
            sort_by: 排序方式 (rating, downloads, recent)
            limit: 返回数量

        Returns:
            技能列表
        """
        listings = list(self._listings.values())

        if category:
            listings = [l for l in listings if l.category == category]

        if sort_by == "rating":
            listings.sort(key=lambda x: x.rating, reverse=True)
        elif sort_by == "downloads":
            listings.sort(key=lambda x: x.download_count, reverse=True)
        elif sort_by == "recent":
            listings.sort(key=lambda x: x.updated_at, reverse=True)

        return listings[:limit]

    def search(self, query: str) -> List[SkillListing]:
        """
        搜索技能

        Args:
            query: 搜索关键词

        Returns:
            匹配的技能列表
        """
        query_lower = query.lower()
        results = []

        for listing in self._listings.values():
            if (query_lower in listing.name.lower() or
                query_lower in listing.description.lower() or
                query_lower in ' '.join(listing.tags).lower()):
                results.append(listing)

        results.sort(key=lambda x: x.rating, reverse=True)
        return results

    def get_listing(self, listing_id: str) -> Optional[SkillListing]:
        """获取技能详情"""
        return self._listings.get(listing_id)

    def install_skill(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """
        安装市场中的技能

        Args:
            listing_id: 技能ID

        Returns:
            技能数据
        """
        listing = self._listings.get(listing_id)
        if not listing:
            return None

        listing.download_count += 1
        self._save_listings()

        return listing.skill_data

    def rate_skill(self, listing_id: str, rating: float) -> bool:
        """
        评分技能

        Args:
            listing_id: 技能ID
            rating: 评分 (1-5)

        Returns:
            是否成功
        """
        listing = self._listings.get(listing_id)
        if not listing:
            return False

        current_total = listing.rating * listing.download_count
        listing.download_count += 1
        listing.rating = (current_total + rating) / listing.download_count

        self._save_listings()
        return True

    def remove_skill(self, listing_id: str) -> bool:
        """从市场移除技能"""
        if listing_id not in self._listings:
            return False

        listing = self._listings[listing_id]
        if listing.manifest_path:
            manifest = Path(listing.manifest_path)
            if manifest.exists():
                manifest.unlink()

        del self._listings[listing_id]
        self._save_listings()
        return True

    def get_categories(self) -> List[str]:
        """获取所有分类"""
        categories = set()
        for listing in self._listings.values():
            categories.add(listing.category)
        return sorted(list(categories))

    def get_stats(self) -> Dict[str, Any]:
        """获取市场统计"""
        total = len(self._listings)
        total_downloads = sum(l.download_count for l in self._listings.values())
        avg_rating = sum(l.rating for l in self._listings.values()) / total if total > 0 else 0

        return {
            'total_skills': total,
            'total_downloads': total_downloads,
            'average_rating': avg_rating,
            'categories': len(self.get_categories())
        }


class SkillHubClient:
    """
    远程技能市场客户端
    支持连接到 agentskills.io 等远程市场
    """

    def __init__(self, hub_url: str = "https://api.agentskills.io"):
        self.hub_url = hub_url.rstrip('/')
        self._cache: Dict[str, Any] = {}
        self._auth_token: Optional[str] = None
        self._version_cache: Dict[str, str] = {}

    def set_auth_token(self, token: str):
        """设置认证令牌"""
        self._auth_token = token

    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
        self._version_cache.clear()

    async def fetch_skill(self, skill_id: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        从远程市场获取技能
        """
        if use_cache and skill_id in self._cache:
            return self._cache[skill_id]

        try:
            import httpx
            headers = {}
            if self._auth_token:
                headers['Authorization'] = f'Bearer {self._auth_token}'

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.hub_url}/skills/{skill_id}",
                    headers=headers,
                    timeout=15.0
                )

                if response.status_code == 200:
                    skill_data = response.json()
                    self._cache[skill_id] = skill_data
                    return skill_data
                elif response.status_code == 404:
                    return None
                else:
                    response.raise_for_status()
        except Exception as e:
            print(f"Error fetching skill: {e}")

        return None

    async def search_remote(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        搜索远程市场
        """
        try:
            import httpx
            params = {
                'q': query,
                'limit': limit
            }
            if category:
                params['category'] = category

            headers = {}
            if self._auth_token:
                headers['Authorization'] = f'Bearer {self._auth_token}'

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.hub_url}/skills/search",
                    params=params,
                    headers=headers,
                    timeout=15.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get('results', [])
        except Exception as e:
            print(f"Error searching remote: {e}")

        return []

    async def publish_remote(
        self,
        skill_data: Dict[str, Any],
        version: str = "1.0.0"
    ) -> Optional[str]:
        """
        发布技能到远程市场
        """
        if not self._auth_token:
            return None

        skill_id = skill_data.get('id', '')
        self._version_cache[skill_id] = version

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.hub_url}/skills",
                    json={
                        "skill": skill_data,
                        "version": version
                    },
                    headers={
                        'Authorization': f'Bearer {self._auth_token}',
                        'Content-Type': 'application/json'
                    },
                    timeout=30.0
                )

                if response.status_code in (200, 201):
                    result = response.json()
                    remote_id = result.get('id', skill_id)
                    self._cache[remote_id] = skill_data
                    return remote_id
        except Exception as e:
            print(f"Error publishing skill: {e}")

        return None

    async def check_version(self, skill_id: str) -> Optional[str]:
        """
        检查远程技能版本
        """
        if skill_id in self._version_cache:
            return self._version_cache[skill_id]

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.head(
                    f"{self.hub_url}/skills/{skill_id}",
                    timeout=10.0
                )

                if response.status_code == 200:
                    version = response.headers.get('X-Skill-Version')
                    if version:
                        self._version_cache[skill_id] = version
                        return version
        except Exception:
            pass

        return None

    async def rate_skill_remote(
        self,
        skill_id: str,
        rating: float
    ) -> bool:
        """
        在远程市场评分
        """
        if not self._auth_token:
            return False

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.hub_url}/skills/{skill_id}/rate",
                    json={"rating": rating},
                    headers={
                        'Authorization': f'Bearer {self._auth_token}'
                    },
                    timeout=10.0
                )

                return response.status_code == 200
        except Exception:
            pass

        return False

    async def get_featured_skills(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取精选技能
        """
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.hub_url}/skills/featured",
                    params={'limit': limit},
                    timeout=15.0
                )

                if response.status_code == 200:
                    return response.json().get('skills', [])
        except Exception:
            pass

        return []
