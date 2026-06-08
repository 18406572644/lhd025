<script>
  import { onMount } from 'svelte';
  import { cornerStore } from '$lib/stores/corners';
  import { auth } from '$lib/stores/auth';
  import { getUserStats } from '$lib/api/auth';
  import CornerCard from '$lib/components/CornerCard.svelte';
  import MapView from '$lib/components/MapView.svelte';
  import Loading from '$lib/components/Loading.svelte';
  import { toast } from '$lib/stores/toast';
  import { goto } from '$app/navigation';

  let featuredCorners = [];
  let loading = true;
  let userStats = null;
  let mapMarkers = [];

  const categories = [
    { name: '人文古迹', icon: '🏛️', color: 'bg-amber-100 text-amber-700' },
    { name: '自然风光', icon: '🌿', color: 'bg-green-100 text-green-700' },
    { name: '文艺空间', icon: '📚', color: 'bg-purple-100 text-purple-700' },
    { name: '艺术创意', icon: '🎨', color: 'bg-pink-100 text-pink-700' },
    { name: '体验工坊', icon: '🛠️', color: 'bg-orange-100 text-orange-700' },
    { name: '美食探店', icon: '🍜', color: 'bg-red-100 text-red-700' },
  ];

  onMount(async () => {
    try {
      const corners = await cornerStore.fetchCorners({ limit: 8 });
      if (corners) {
        featuredCorners = corners;
        mapMarkers = corners.map(c => ({
          latitude: c.latitude,
          longitude: c.longitude,
          title: c.title,
          content: c.description.substring(0, 50) + '...',
          onClick: () => goto(`/corners/${c.id}`)
        }));
      }

      if ($auth.isAuthenticated) {
        userStats = await getUserStats();
      }
    } catch (error) {
      toast.error('加载数据失败');
    } finally {
      loading = false;
    }
  });

  function handleCategoryClick(category) {
    goto(`/corners?category=${encodeURIComponent(category)}`);
  }
</script>

{#if loading}
  <Loading fullscreen text="正在探索城市角落..." />
{:else}
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <!-- Hero Section -->
    <section class="relative py-16 md:py-24 overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-r from-primary-500/10 via-sky-500/10 to-primary-500/10 rounded-3xl"></div>
      <div class="relative z-10 text-center">
        <div class="text-6xl md:text-7xl mb-6 animate-bounce-soft">🌿</div>
        <h1 class="text-4xl md:text-5xl lg:text-6xl font-bold text-natural-800 mb-4">
          发现城市里的
          <span class="gradient-text">小众角落</span>
        </h1>
        <p class="text-lg md:text-xl text-natural-600 max-w-2xl mx-auto mb-8">
          探索那些被遗忘的美好，记录你的每一次发现，与志同道合的探索者一起分享
        </p>
        <div class="flex flex-wrap justify-center gap-4">
          <a href="/corners" class="btn btn-primary px-8 py-3 text-lg">
            🔍 开始探索
          </a>
          {#if !$auth.isAuthenticated}
            <a href="/register" class="btn btn-secondary px-8 py-3 text-lg">
              🌟 加入我们
            </a>
          {/if}
        </div>
      </div>
    </section>

    <!-- User Stats -->
    {#if $auth.isAuthenticated && userStats}
      <section class="mb-12">
        <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div class="card p-5 text-center">
            <div class="text-3xl mb-2">📍</div>
            <div class="text-2xl font-bold text-primary-600">{userStats.total_corners}</div>
            <div class="text-sm text-natural-500">发布角落</div>
          </div>
          <div class="card p-5 text-center">
            <div class="text-3xl mb-2">✅</div>
            <div class="text-2xl font-bold text-sky-600">{userStats.total_checkins}</div>
            <div class="text-sm text-natural-500">打卡记录</div>
          </div>
          <div class="card p-5 text-center">
            <div class="text-3xl mb-2">🗺️</div>
            <div class="text-2xl font-bold text-amber-600">{userStats.total_routes}</div>
            <div class="text-sm text-natural-500">路线规划</div>
          </div>
          <div class="card p-5 text-center">
            <div class="text-3xl mb-2">🏆</div>
            <div class="text-2xl font-bold text-purple-600">{userStats.total_achievements}</div>
            <div class="text-sm text-natural-500">获得成就</div>
          </div>
          <div class="card p-5 text-center col-span-2 md:col-span-1">
            <div class="text-3xl mb-2">📤</div>
            <div class="text-2xl font-bold text-pink-600">{userStats.total_shares}</div>
            <div class="text-sm text-natural-500">分享次数</div>
          </div>
        </div>
      </section>
    {/if}

    <!-- Categories -->
    <section class="mb-12">
      <h2 class="section-title">
        <span>📂</span>
        探索分类
      </h2>
      <div class="grid grid-cols-3 md:grid-cols-6 gap-4">
        {#each categories as cat}
          <button
            on:click={() => handleCategoryClick(cat.name)}
            class="card p-4 text-center hover:scale-105 transition-transform"
          >
            <div class="text-4xl mb-2">{cat.icon}</div>
            <span class="badge {cat.color}">{cat.name}</span>
          </button>
        {/each}
      </div>
    </section>

    <!-- Featured Corners Map -->
    <section class="mb-12">
      <h2 class="section-title">
        <span>🗺️</span>
        角落地图
      </h2>
      <div class="card p-4">
        <div class="h-96">
          <MapView
            markers={mapMarkers}
            center={[39.9342, 116.4374]}
            zoom={12}
          />
        </div>
      </div>
    </section>

    <!-- Featured Corners -->
    <section class="mb-12">
      <div class="flex items-center justify-between mb-6">
        <h2 class="section-title mb-0">
          <span>✨</span>
          精选角落
        </h2>
        <a href="/corners" class="text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1">
          查看全部
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
          </svg>
        </a>
      </div>
      
      {#if featuredCorners.length > 0}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {#each featuredCorners as corner}
            <CornerCard {corner} />
          {/each}
        </div>
      {:else}
        <div class="card p-12 text-center">
          <div class="text-5xl mb-4">🌱</div>
          <p class="text-natural-600 mb-4">还没有角落被发现，成为第一个探索者吧！</p>
          {#if $auth.isAuthenticated}
            <a href="/publish" class="btn btn-primary">发布第一个角落</a>
          {/if}
        </div>
      {/if}
    </section>

    <!-- CTA Section -->
    <section class="mb-12">
      <div class="card bg-gradient-to-r from-primary-500 to-sky-500 text-white p-8 md:p-12 text-center">
        <div class="text-5xl mb-4">🌟</div>
        <h2 class="text-3xl font-bold mb-4">有你发现的小众角落吗？</h2>
        <p class="text-white/90 max-w-xl mx-auto mb-6">
          分享你发现的城市秘密，让更多人感受到这些隐藏的美好
        </p>
        {#if $auth.isAuthenticated}
          <a href="/publish" class="btn bg-white text-primary-600 hover:bg-natural-100 px-8 py-3 text-lg">
            + 发布角落
          </a>
        {:else}
          <a href="/login" class="btn bg-white text-primary-600 hover:bg-natural-100 px-8 py-3 text-lg">
            登录发布
          </a>
        {/if}
      </div>
    </section>
  </div>
{/if}
