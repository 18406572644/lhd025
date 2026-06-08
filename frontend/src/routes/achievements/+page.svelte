<script>
  import { onMount } from 'svelte';
  import { auth } from '$lib/stores/auth';
  import { getAchievements, getUserAchievements } from '$lib/api/achievements';
  import Loading from '$lib/components/Loading.svelte';
  import { toast } from '$lib/stores/toast';

  let allAchievements = [];
  let userAchievements = [];
  let loading = true;
  let filter = 'all';

  const filters = [
    { value: 'all', label: '全部成就' },
    { value: 'unlocked', label: '已解锁' },
    { value: 'locked', label: '未解锁' }
  ];

  $: filteredAchievements = allAchievements.map(achievement => {
    const userAchievement = userAchievements.find(ua => ua.achievement?.id === achievement.id);
    return {
      ...achievement,
      isUnlocked: !!userAchievement,
      unlockedAt: userAchievement?.unlocked_at,
      progress: userAchievement?.progress || 0
    };
  }).filter(achievement => {
    if (filter === 'unlocked') return achievement.isUnlocked;
    if (filter === 'locked') return !achievement.isUnlocked;
    return true;
  });

  $: unlockedCount = allAchievements.filter(a => 
    userAchievements.some(ua => ua.achievement?.id === a.id)
  ).length;

  $: totalCount = allAchievements.length;

  $: progressPercentage = totalCount > 0 ? Math.round((unlockedCount / totalCount) * 100) : 0;

  onMount(async () => {
    await loadAchievements();
  });

  async function loadAchievements() {
    loading = true;
    try {
      let achievementsData = [];
      let userData = [];
      
      try {
        achievementsData = await getAchievements() || [];
      } catch (e) {
        console.error('Failed to load achievements:', e);
      }
      
      try {
        if ($auth.isAuthenticated) {
          userData = await getUserAchievements() || [];
        }
      } catch (e) {
        console.error('Failed to load user achievements:', e);
      }
      
      allAchievements = achievementsData;
      userAchievements = userData;
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

  function getConditionText(achievement) {
    const typeMap = {
      checkin_count: '打卡次数',
      corner_count: '发现角落数',
      category_count: '分类探索数',
      share_count: '分享次数',
      consecutive_days: '连续打卡天数',
      total_points: '累计积分'
    };
    const typeText = typeMap[achievement.condition_type] || achievement.condition_type;
    return `${typeText}达到 ${achievement.condition_value}`;
  }

  function getProgressText(achievement) {
    if (achievement.isUnlocked) return '已完成';
    const current = achievement.progress || 0;
    const total = achievement.condition_value;
    return `${current} / ${total}`;
  }

  function getProgressPercentage(achievement) {
    if (achievement.isUnlocked) return 100;
    const current = achievement.progress || 0;
    const total = achievement.condition_value;
    return Math.min(Math.round((current / total) * 100), 100);
  }
</script>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-natural-800 mb-2">成就中心</h1>
    <p class="text-natural-600">探索城市，解锁成就，记录你的每一步成长</p>
  </div>

  <!-- Progress Overview -->
  <div class="card p-6 mb-8">
    <div class="flex flex-col md:flex-row items-center gap-6">
      <div class="w-24 h-24 relative flex-shrink-0">
        <svg class="w-full h-full transform -rotate-90">
          <circle
            cx="48"
            cy="48"
            r="40"
            stroke="currentColor"
            stroke-width="8"
            fill="none"
            class="text-natural-100"
          />
          <circle
            cx="48"
            cy="48"
            r="40"
            stroke="currentColor"
            stroke-width="8"
            fill="none"
            stroke-linecap="round"
            class="text-primary-500 transition-all duration-1000"
            style="stroke-dasharray: 251.2; stroke-dashoffset: {251.2 - (251.2 * progressPercentage / 100)}"
          />
        </svg>
        <div class="absolute inset-0 flex items-center justify-center">
          <span class="text-2xl font-bold text-natural-800">{progressPercentage}%</span>
        </div>
      </div>
      
      <div class="flex-1 text-center md:text-left">
        <h2 class="text-xl font-bold text-natural-800 mb-2">
          已解锁 <span class="gradient-text">{unlockedCount}</span> / {totalCount} 个成就
        </h2>
        <p class="text-natural-600 mb-4">
          {#if progressPercentage === 100}
            🎉 恭喜！你已经解锁了所有成就！
          {:else if progressPercentage >= 50}
            👍 太棒了！已经完成一半以上，继续加油！
          {:else if progressPercentage > 0}
            💪 继续探索，解锁更多成就吧！
          {:else}
            🌟 开始你的探索之旅，解锁第一个成就吧！
          {/if}
        </p>
        {#if !$auth.isAuthenticated}
          <p class="text-amber-600 text-sm">
            ⚠️ 请先登录以查看和追踪你的成就进度
          </p>
        {/if}
      </div>
    </div>
  </div>

  <!-- Filter Tabs -->
  <div class="flex flex-wrap gap-2 mb-6">
    {#each filters as f}
      <button
        on:click={() => handleFilterChange(f.value)}
        class="px-4 py-2 rounded-full text-sm font-medium transition-all {filter === f.value
          ? 'bg-primary-500 text-white shadow-soft'
          : 'bg-white text-natural-600 hover:bg-primary-50 hover:text-primary-600 border border-natural-200'}"
      >
        {f.label}
        {#if f.value === 'unlocked'}
          <span class="ml-1">({unlockedCount})</span>
        {:else if f.value === 'locked'}
          <span class="ml-1">({totalCount - unlockedCount})</span>
        {:else}
          <span class="ml-1">({totalCount})</span>
        {/if}
      </button>
    {/each}
  </div>

  {#if loading}
    <Loading text="正在加载成就列表..." />
  {:else if filteredAchievements.length > 0}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {#each filteredAchievements as achievement}
        <div class="card group {achievement.isUnlocked ? '' : 'opacity-75'}">
          <div class="p-6">
            <div class="flex items-start gap-4">
              <div class="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl flex-shrink-0 transition-transform group-hover:scale-110 {achievement.isUnlocked
                ? 'bg-gradient-to-br from-primary-400 to-sky-400 shadow-lg'
                : 'bg-natural-100'}">
                {#if achievement.isUnlocked}
                  {achievement.icon}
                {:else}
                  <span class="opacity-50">{achievement.icon}</span>
                {/if}
              </div>
              
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <h3 class="font-bold text-natural-800 truncate">{achievement.name}</h3>
                  {#if achievement.isUnlocked}
                    <span class="badge bg-green-100 text-green-700">
                      ✅ 已解锁
                    </span>
                  {:else}
                    <span class="badge bg-natural-100 text-natural-500">
                      🔒 未解锁
                    </span>
                  {/if}
                </div>
                <p class="text-sm text-natural-600 line-clamp-2 mb-3">
                  {achievement.description}
                </p>
                <p class="text-xs text-natural-500 mb-3">
                  🎯 {getConditionText(achievement)}
                </p>
              </div>
            </div>
            
            <!-- Progress Bar -->
            <div class="mt-4">
              <div class="flex items-center justify-between text-sm mb-2">
                <span class="text-natural-600">
                  {achievement.isUnlocked ? '完成度' : '当前进度'}
                </span>
                <span class="font-medium {achievement.isUnlocked ? 'text-green-600' : 'text-primary-600'}">
                  {getProgressText(achievement)}
                </span>
              </div>
              <div class="h-2 bg-natural-100 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500 {achievement.isUnlocked
                    ? 'bg-gradient-to-r from-green-400 to-green-500'
                    : 'bg-gradient-to-r from-primary-400 to-sky-400'}"
                  style="width: {getProgressPercentage(achievement)}%"
                />
              </div>
              {#if achievement.unlockedAt}
                <p class="text-xs text-natural-500 mt-2">
                  📅 解锁于 {new Date(achievement.unlockedAt).toLocaleDateString('zh-CN')}
                </p>
              {/if}
            </div>
          </div>
        </div>
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
            : '暂无成就数据'}
      </p>
      {#if filter !== 'all'}
        <button on:click={() => handleFilterChange('all')} class="btn btn-primary">
          查看全部成就
        </button>
      {/if}
    </div>
  {/if}
</div>
