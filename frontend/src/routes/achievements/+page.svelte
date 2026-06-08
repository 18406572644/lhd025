<script>
  import { onMount } from 'svelte';
  import { auth } from '$lib/stores/auth';
  import { achievements as achievementStore } from '$lib/stores/achievements';
  import { getAchievements, getUserAchievements, getUserAchievementStats, getRarityConfig, getLevelConfig } from '$lib/api/achievements';
  import Loading from '$lib/components/Loading.svelte';
  import AchievementCard from '$lib/components/AchievementCard.svelte';
  import AchievementUnlockModal from '$lib/components/AchievementUnlockModal.svelte';
  import { toast } from '$lib/stores/toast';

  let allAchievements = [];
  let userAchievements = [];
  let userStats = null;
  let rarityConfig = {};
  let levelConfig = [];
  let loading = true;
  let filter = 'all';
  let rarityFilter = 'all';
  let sortBy = 'rarity';
  let unlockModalOpen = false;
  let currentUnlockAchievement = null;

  const filters = [
    { value: 'all', label: '全部成就', icon: '🏆' },
    { value: 'unlocked', label: '已解锁', icon: '✅' },
    { value: 'locked', label: '未解锁', icon: '🔒' }
  ];

  const rarityFilters = [
    { value: 'all', label: '全部稀有度', color: '#6B7280' },
    { value: 'common', label: '普通', color: '#9CA3AF', icon: '⚪' },
    { value: 'rare', label: '稀有', color: '#22C55E', icon: '🟢' },
    { value: 'epic', label: '史诗', color: '#A855F7', icon: '🟣' },
    { value: 'legendary', label: '传说', color: '#F97316', icon: '🟠' },
    { value: 'mythic', label: '神话', color: '#EF4444', icon: '🔴' }
  ];

  const sortOptions = [
    { value: 'rarity', label: '按稀有度' },
    { value: 'progress', label: '按进度' },
    { value: 'unlocked', label: '按解锁时间' }
  ];

  $: mergedAchievements = userAchievements.map(ua => ({
    ...ua,
    achievement: allAchievements.find(a => a.id === ua.achievement?.id) || ua.achievement
  }));

  $: filteredAchievements = mergedAchievements.filter(ua => {
    if (filter === 'unlocked' && !ua.is_unlocked) return false;
    if (filter === 'locked' && ua.is_unlocked) return false;
    if (rarityFilter !== 'all' && ua.achievement?.rarity !== rarityFilter) return false;
    return true;
  });

  $: sortedAchievements = [...filteredAchievements].sort((a, b) => {
    if (sortBy === 'rarity') {
      const rarityOrder = ['mythic', 'legendary', 'epic', 'rare', 'common'];
      return rarityOrder.indexOf(a.achievement?.rarity) - rarityOrder.indexOf(b.achievement?.rarity);
    } else if (sortBy === 'progress') {
      const progressA = (a.progress / (a.achievement?.condition_value || 1)) * 100;
      const progressB = (b.progress / (b.achievement?.condition_value || 1)) * 100;
      return progressB - progressA;
    } else if (sortBy === 'unlocked') {
      if (a.is_unlocked && !b.is_unlocked) return -1;
      if (!a.is_unlocked && b.is_unlocked) return 1;
      if (a.unlocked_at && b.unlocked_at) {
        return new Date(b.unlocked_at) - new Date(a.unlocked_at);
      }
      return 0;
    }
    return 0;
  });

  $: unlockedCount = userAchievements.filter(ua => ua.is_unlocked).length;
  $: totalCount = allAchievements.length;
  $: progressPercentage = totalCount > 0 ? Math.round((unlockedCount / totalCount) * 100) : 0;

  $: rarityCounts = {
    common: userAchievements.filter(ua => ua.is_unlocked && ua.achievement?.rarity === 'common').length,
    rare: userAchievements.filter(ua => ua.is_unlocked && ua.achievement?.rarity === 'rare').length,
    epic: userAchievements.filter(ua => ua.is_unlocked && ua.achievement?.rarity === 'epic').length,
    legendary: userAchievements.filter(ua => ua.is_unlocked && ua.achievement?.rarity === 'legendary').length,
    mythic: userAchievements.filter(ua => ua.is_unlocked && ua.achievement?.rarity === 'mythic').length
  };

  onMount(async () => {
    window.addEventListener('achievement:unlock', handleAchievementUnlock);
    await loadAchievements();
  });

  function handleAchievementUnlock(event) {
    currentUnlockAchievement = event.detail;
    unlockModalOpen = true;
    loadAchievements();
  }

  async function loadAchievements() {
    loading = true;
    try {
      const [achievementsData, userData, statsData, rarityData, levelData] = await Promise.all([
        getAchievements() || [],
        $auth.isAuthenticated ? getUserAchievements() || [] : [],
        $auth.isAuthenticated ? getUserAchievementStats() : null,
        getRarityConfig(),
        getLevelConfig()
      ]);
      
      allAchievements = achievementsData;
      userAchievements = userData;
      userStats = statsData;
      rarityConfig = rarityData;
      levelConfig = levelData;
    } catch (error) {
      console.error('Failed to load achievements:', error);
      toast.error('加载成就列表失败');
    } finally {
      loading = false;
    }
  }

  function handleFilterChange(value) {
    filter = value;
  }

  function handleRarityFilterChange(value) {
    rarityFilter = value;
  }

  function handleSortChange(value) {
    sortBy = value;
  }

  function getRarityInfo(rarity) {
    return rarityConfig[rarity] || rarityConfig.common;
  }

  function getLevelInfo() {
    if (!userStats) return null;
    return levelConfig.find(l => l.level === userStats.level) || levelConfig[0];
  }

  function getNextLevelInfo() {
    if (!userStats) return null;
    const currentIndex = levelConfig.findIndex(l => l.level === userStats.level);
    return levelConfig[currentIndex + 1] || null;
  }
</script>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 md:pb-8">
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-natural-800 mb-2">🏆 成就中心</h1>
    <p class="text-natural-600">探索城市，解锁成就，记录你的每一步成长</p>
  </div>

  {#if loading}
    <Loading text="正在加载成就列表..." />
  {:else}
    {#if $auth.isAuthenticated && userStats}
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="card p-6 bg-gradient-to-br from-primary-50 to-sky-50">
          <div class="flex items-center gap-4">
            <div class="w-16 h-16 rounded-2xl bg-white flex items-center justify-center text-4xl shadow-soft">
              {getLevelInfo()?.icon || '🥉'}
            </div>
            <div class="flex-1">
              <div class="text-sm text-natural-500 mb-1">当前等级</div>
              <div class="text-2xl font-bold text-natural-800">{userStats.level_name}</div>
              <div class="text-sm text-primary-600 font-medium">
                累计 {userStats.total_points} 点
              </div>
            </div>
          </div>
          {#if getNextLevelInfo()}
            <div class="mt-4">
              <div class="flex items-center justify-between text-sm mb-2">
                <span class="text-natural-500">
                  距离 {getNextLevelInfo()?.name}
                </span>
                <span class="text-primary-600 font-medium">
                  还需 {userStats.next_level_points} 点
                </span>
              </div>
              <div class="h-2 bg-white/50 rounded-full overflow-hidden">
                <div
                  class="h-full bg-gradient-to-r from-primary-500 to-sky-500 rounded-full transition-all duration-500"
                  style="width: {userStats.current_level_progress}%"
                />
              </div>
            </div>
          {/if}
        </div>

        <div class="card p-6">
          <div class="flex items-center gap-4 mb-4">
            <div class="w-20 h-20 relative flex-shrink-0">
              <svg class="w-full h-full transform -rotate-90">
                <circle
                  cx="40"
                  cy="40"
                  r="32"
                  stroke="currentColor"
                  stroke-width="6"
                  fill="none"
                  class="text-natural-100"
                />
                <circle
                  cx="40"
                  cy="40"
                  r="32"
                  stroke="currentColor"
                  stroke-width="6"
                  fill="none"
                  stroke-linecap="round"
                  class="text-primary-500 transition-all duration-1000"
                  style="stroke-dasharray: 201; stroke-dashoffset: {201 - (201 * progressPercentage / 100)}"
                />
              </svg>
              <div class="absolute inset-0 flex items-center justify-center">
                <span class="text-xl font-bold text-natural-800">{progressPercentage}%</span>
              </div>
            </div>
            <div>
              <div class="text-2xl font-bold text-natural-800">
                <span class="gradient-text">{unlockedCount}</span> / {totalCount}
              </div>
              <div class="text-sm text-natural-500">已解锁成就</div>
            </div>
          </div>
          
          <div class="grid grid-cols-5 gap-2">
            {#each rarityFilters.slice(1) as rarity}
              <div class="text-center">
                <div
                  class="text-lg font-bold"
                  style="color: {rarity.color}"
                >
                  {rarityCounts[rarity.value]}
                </div>
                <div class="text-xs text-natural-500">{rarity.icon}</div>
              </div>
            {/each}
          </div>
        </div>

        <div class="card p-6">
          <div class="text-sm text-natural-500 mb-3">成就点数分布</div>
          <div class="space-y-3">
            {#each rarityFilters.slice(1) as rarity}
              {@const count = rarityCounts[rarity.value]}
              {@const points = count * (getRarityInfo(rarity.value)?.points || 0)}
              {@const maxPoints = rarityCounts.mythic * 200}
              {@const width = maxPoints > 0 ? (points / maxPoints) * 100 : 0}
              <div class="flex items-center gap-3">
                <span class="text-lg w-6">{rarity.icon}</span>
                <div class="flex-1">
                  <div class="h-2 bg-natural-100 rounded-full overflow-hidden">
                    <div
                      class="h-full rounded-full transition-all duration-500"
                      style="width: {width}%; background: {rarity.color}"
                    />
                  </div>
                </div>
                <span class="text-sm font-medium text-natural-700 w-12 text-right">
                  {points} 点
                </span>
              </div>
            {/each}
          </div>
        </div>
      </div>
    {:else if !$auth.isAuthenticated}
      <div class="card p-8 mb-8 bg-gradient-to-r from-primary-50 to-sky-50 text-center">
        <div class="text-5xl mb-4">🔒</div>
        <h2 class="text-xl font-bold text-natural-800 mb-2">登录以追踪你的成就</h2>
        <p class="text-natural-600 mb-4">登录后即可查看你的成就进度、解锁记录和排名</p>
        <a href="/login" class="btn btn-primary inline-flex items-center gap-2">
          立即登录
        </a>
      </div>
    {/if}

    <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
      <div class="flex flex-wrap gap-2">
        {#each filters as f}
          <button
            on:click={() => handleFilterChange(f.value)}
            class="px-4 py-2 rounded-full text-sm font-medium transition-all flex items-center gap-2 {filter === f.value
              ? 'bg-primary-500 text-white shadow-soft'
              : 'bg-white text-natural-600 hover:bg-primary-50 hover:text-primary-600 border border-natural-200'}"
          >
            <span>{f.icon}</span>
            <span>{f.label}</span>
            {#if f.value === 'unlocked'}
              <span class="text-xs opacity-80">({unlockedCount})</span>
            {:else if f.value === 'locked'}
              <span class="text-xs opacity-80">({totalCount - unlockedCount})</span>
            {:else}
              <span class="text-xs opacity-80">({totalCount})</span>
            {/if}
          </button>
        {/each}
      </div>

      <div class="flex flex-wrap gap-2">
        <select
          bind:value={sortBy}
          on:change={(e) => handleSortChange(e.target.value)}
          class="px-4 py-2 rounded-xl text-sm font-medium border border-natural-200 bg-white text-natural-700 focus:border-primary-400 focus:ring-2 focus:ring-primary-100 outline-none"
        >
          {#each sortOptions as option}
            <option value={option.value}>{option.label}</option>
          {/each}
        </select>
      </div>
    </div>

    <div class="flex flex-wrap gap-2 mb-6">
      {#each rarityFilters as rarity}
        <button
          on:click={() => handleRarityFilterChange(rarity.value)}
          class="px-3 py-1.5 rounded-full text-sm font-medium transition-all flex items-center gap-1.5 {rarityFilter === rarity.value
            ? 'text-white shadow-soft'
            : 'bg-white text-natural-600 hover:bg-natural-50 border border-natural-200'}"
          style={rarityFilter === rarity.value ? `background: ${rarity.color}` : ''}
        >
          {#if rarity.icon}
            <span>{rarity.icon}</span>
          {/if}
          <span>{rarity.label}</span>
        </button>
      {/each}
    </div>

    {#if sortedAchievements.length > 0}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {#each sortedAchievements as ua}
          <AchievementCard achievement={ua} />
        {/each}
      </div>
    {:else}
      <div class="card p-12 text-center">
        <div class="text-5xl mb-4">🏆</div>
        <p class="text-natural-600 mb-4">
          {filter === 'unlocked'
            ? '还没有解锁任何成就，快去探索吧！'
            : filter === 'locked'
              ? '太棒了！你已经解锁了所有成就！'
              : rarityFilter !== 'all'
                ? `还没有${rarityFilters.find(r => r.value === rarityFilter)?.label}成就`
                : '暂无成就数据'}
        </p>
        {#if filter !== 'all' || rarityFilter !== 'all'}
          <button on:click={() => { filter = 'all'; rarityFilter = 'all'; }} class="btn btn-primary">
            查看全部成就
          </button>
        {/if}
      </div>
    {/if}
  {/if}
</div>

<AchievementUnlockModal
  bind:isOpen={unlockModalOpen}
  bind:achievement={currentUnlockAchievement}
/>
