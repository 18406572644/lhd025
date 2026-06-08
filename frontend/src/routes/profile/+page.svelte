<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { auth } from '$lib/stores/auth';
  import { achievements as achievementStore } from '$lib/stores/achievements';
  import { getUserStats } from '$lib/api/auth';
  import { getUserAchievements, getUserAchievementStats, getLevelConfig, getRarityConfig } from '$lib/api/achievements';
  import Loading from '$lib/components/Loading.svelte';
  import AchievementCard from '$lib/components/AchievementCard.svelte';
  import AchievementUnlockModal from '$lib/components/AchievementUnlockModal.svelte';
  import { toast } from '$lib/stores/toast';

  let stats = null;
  let userAchievements = [];
  let achievementStats = null;
  let levelConfig = [];
  let rarityConfig = {};
  let loading = true;
  let activeTab = 'overview';
  let editing = false;
  let formData = {
    username: '',
    email: '',
    bio: '',
    avatar: '',
  };

  const tabs = [
    { id: 'overview', label: '总览', icon: '📊' },
    { id: 'achievements', label: '成就墙', icon: '🏆' },
    { id: 'settings', label: '设置', icon: '⚙️' }
  ];

  let unlockModalOpen = false;
  let currentUnlockAchievement = null;

  const rarityFilters = [
    { value: 'all', label: '全部稀有度', color: '#6B7280' },
    { value: 'common', label: '普通', color: '#9CA3AF', icon: '⚪' },
    { value: 'rare', label: '稀有', color: '#22C55E', icon: '🟢' },
    { value: 'epic', label: '史诗', color: '#A855F7', icon: '🟣' },
    { value: 'legendary', label: '传说', color: '#F97316', icon: '🟠' },
    { value: 'mythic', label: '神话', color: '#EF4444', icon: '🔴' }
  ];

  let rarityFilter = 'all';

  $: sortedAchievements = [...userAchievements]
    .filter(ua => ua.is_unlocked)
    .filter(ua => rarityFilter === 'all' || ua.achievement?.rarity === rarityFilter)
    .sort((a, b) => {
      const rarityOrder = ['mythic', 'legendary', 'epic', 'rare', 'common'];
      return rarityOrder.indexOf(a.achievement?.rarity) - rarityOrder.indexOf(b.achievement?.rarity);
    });

  $: unlockedCount = userAchievements.filter(ua => ua.is_unlocked).length;
  $: rarityCounts = {
    common: userAchievements.filter(ua => ua.is_unlocked && ua.achievement?.rarity === 'common').length,
    rare: userAchievements.filter(ua => ua.is_unlocked && ua.achievement?.rarity === 'rare').length,
    epic: userAchievements.filter(ua => ua.is_unlocked && ua.achievement?.rarity === 'epic').length,
    legendary: userAchievements.filter(ua => ua.is_unlocked && ua.achievement?.rarity === 'legendary').length,
    mythic: userAchievements.filter(ua => ua.is_unlocked && ua.achievement?.rarity === 'mythic').length
  };

  function getLevelInfo() {
    if (!achievementStats) return null;
    return levelConfig.find(l => l.level === achievementStats.level) || levelConfig[0];
  }

  function getNextLevelInfo() {
    if (!achievementStats) return null;
    const currentIndex = levelConfig.findIndex(l => l.level === achievementStats.level);
    return levelConfig[currentIndex + 1] || null;
  }

  function getRarityInfo(rarity) {
    return rarityConfig[rarity] || rarityConfig.common;
  }

  onMount(async () => {
    window.addEventListener('achievement:unlock', handleAchievementUnlock);
    
    if (!$auth.isAuthenticated) {
      goto('/login');
      return;
    }
    
    await loadData();
  });

  function handleAchievementUnlock(event) {
    currentUnlockAchievement = event.detail;
    unlockModalOpen = true;
    loadData();
  }

  async function loadData() {
    loading = true;
    try {
      const [statsData, achData, achStats, levelData, rarityData] = await Promise.all([
        getUserStats(),
        getUserAchievements() || [],
        getUserAchievementStats(),
        getLevelConfig(),
        getRarityConfig()
      ]);
      
      stats = statsData;
      userAchievements = achData;
      achievementStats = achStats;
      levelConfig = levelData;
      rarityConfig = rarityData;
      
      formData = {
        username: $auth.user?.username || '',
        email: $auth.user?.email || '',
        bio: $auth.user?.bio || '',
        avatar: $auth.user?.avatar || '',
      };
    } catch (error) {
      console.error('Failed to load profile:', error);
      toast.error('加载个人信息失败');
    } finally {
      loading = false;
    }
  }

  async function saveProfile() {
    try {
      const response = await auth.updateProfile(formData);
      if (response.success) {
        editing = false;
        toast.success('个人信息更新成功');
        await $auth.fetchCurrentUser();
      } else {
        toast.error(response.error || '更新失败');
      }
    } catch (error) {
      toast.error('更新失败，请重试');
    }
  }

  function handleLogout() {
    if (confirm('确定要退出登录吗？')) {
      auth.logout();
      goto('/login');
    }
  }

  function getTopAchievements() {
    return [...userAchievements]
      .filter(ua => ua.is_unlocked)
      .sort((a, b) => {
        const rarityOrder = ['mythic', 'legendary', 'epic', 'rare', 'common'];
        return rarityOrder.indexOf(a.achievement?.rarity) - rarityOrder.indexOf(b.achievement?.rarity);
      })
      .slice(0, 6);
  }
</script>

<div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-20 md:pb-8">
  {#if loading}
    <Loading text="加载中..." fullscreen={true} />
  {:else if !$auth.isAuthenticated}
    <div class="card p-12 text-center">
      <div class="text-5xl mb-4">🔒</div>
      <h2 class="text-xl font-bold text-natural-800 mb-2">请先登录</h2>
      <p class="text-natural-600 mb-4">登录后即可查看个人主页</p>
      <button on:click={() => goto('/login')} class="btn btn-primary">
        去登录
      </button>
    </div>
  {:else}
    <div class="card overflow-hidden mb-8">
      <div class="h-32 bg-gradient-to-r from-primary-500 to-sky-500 relative">
        <div class="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4xIj48cGF0aCBkPSJNMzYgMzRoLTJ2LTRoMnY0em0tNiAwaC0ydi00aDJ2NHptLTYgMGgtMnYtNGgydjR6bTEyLTZoLTJ2LTRoMnY0em0tNiAwaC0ydi00aDJ2NHptLTYgMGgtMnYtNGgydjR6Ii8+PC9nPjwvZz48L3N2Zz4=')] opacity-30"></div>
      </div>
      
      <div class="px-6 pb-6 relative">
        <div class="flex flex-col md:flex-row md:items-end gap-4 -mt-16">
          <div class="relative">
            <img
              src={$auth.user?.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${$auth.user?.username}`}
              alt="头像"
              class="w-32 h-32 rounded-2xl object-cover border-4 border-white shadow-soft"
            />
            {#if getLevelInfo()}
              <div class="absolute -bottom-2 -right-2 w-10 h-10 rounded-xl bg-white shadow-soft flex items-center justify-center text-2xl">
                {getLevelInfo()?.icon}
              </div>
            {/if}
          </div>
          
          <div class="flex-1">
            <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <h1 class="text-2xl font-bold text-natural-800">
                  {$auth.user?.username}
                  {#if getLevelInfo()}
                    <span class="ml-2 text-base font-normal text-natural-500">
                      {getLevelInfo()?.name}
                    </span>
                  {/if}
                </h1>
                <p class="text-natural-500">
                  {$auth.user?.email}
                </p>
                {#if $auth.user?.bio}
                  <p class="text-natural-600 mt-2">{$auth.user?.bio}</p>
                {/if}
              </div>
              
              <div class="flex gap-3">
                <button on:click={() => editing = true} class="btn btn-outline">
                  ✏️ 编辑资料
                </button>
                <button on:click={handleLogout} class="btn btn-outline text-red-500 border-red-200 hover:border-red-400 hover:text-red-600">
                  🚪 退出登录
                </button>
              </div>
            </div>
          </div>
        </div>
        
        {#if achievementStats}
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8 pt-6 border-t border-natural-100">
            <div class="text-center">
              <div class="text-3xl font-bold gradient-text">{stats?.checkins_count || 0}</div>
              <div class="text-sm text-natural-500">打卡次数</div>
            </div>
            <div class="text-center">
              <div class="text-3xl font-bold text-green-600">{stats?.corners_count || 0}</div>
              <div class="text-sm text-natural-500">发布角落</div>
            </div>
            <div class="text-center">
              <div class="text-3xl font-bold text-purple-600">{unlockedCount}</div>
              <div class="text-sm text-natural-500">解锁成就</div>
            </div>
            <div class="text-center">
              <div class="text-3xl font-bold text-orange-600">{achievementStats.total_points}</div>
              <div class="text-sm text-natural-500">成就点数</div>
            </div>
          </div>
          
          {#if getNextLevelInfo()}
            <div class="mt-6 p-4 bg-gradient-to-r from-primary-50 to-sky-50 rounded-xl">
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-natural-700">
                  {getLevelInfo()?.icon} {getLevelInfo()?.name}
                </span>
                <span class="text-sm text-primary-600 font-medium">
                  距离 {getNextLevelInfo()?.name} 还需 {achievementStats.next_level_points} 点
                </span>
              </div>
              <div class="h-3 bg-white/60 rounded-full overflow-hidden">
                <div
                  class="h-full bg-gradient-to-r from-primary-500 to-sky-500 rounded-full transition-all duration-500"
                  style="width: {achievementStats.current_level_progress}%"
                />
              </div>
            </div>
          {/if}
        {/if}
      </div>
    </div>
    
    <div class="flex gap-2 mb-6 border-b border-natural-200 pb-1 overflow-x-auto">
      {#each tabs as tab}
        <button
          on:click={() => activeTab = tab.id}
          class="px-6 py-3 text-sm font-medium whitespace-nowrap transition-all flex items-center gap-2 {activeTab === tab.id
            ? 'text-primary-600 border-b-2 border-primary-500'
            : 'text-natural-500 hover:text-natural-700'}"
        >
          <span>{tab.icon}</span>
          <span>{tab.label}</span>
        </button>
      {/each}
    </div>
    
    {#if activeTab === 'overview'}
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 space-y-6">
          {#if achievementStats}
            <div class="card p-6">
              <h2 class="section-title">🏆 成就进度</h2>
              <div class="flex items-center justify-between mb-4">
                <div>
                  <span class="text-3xl font-bold gradient-text">{unlockedCount}</span>
                  <span class="text-natural-500"> / {userAchievements.length} 个成就</span>
                </div>
                <button on:click={() => activeTab = 'achievements'} class="text-primary-600 text-sm font-medium hover:underline">
                  查看全部 →
                </button>
              </div>
              
              <div class="h-3 bg-natural-100 rounded-full overflow-hidden mb-6">
                <div
                  class="h-full bg-gradient-to-r from-primary-500 to-sky-500 rounded-full transition-all duration-500"
                  style="width: {userAchievements.length > 0 ? (unlockedCount / userAchievements.length * 100) : 0}%"
                />
              </div>
              
              <div class="grid grid-cols-5 gap-2">
                {#each rarityFilters.slice(1) as rarity}
                  <div class="text-center">
                    <div
                      class="text-2xl font-bold"
                      style="color: {rarity.color}"
                    >
                      {rarityCounts[rarity.value]}
                    </div>
                    <div class="text-xs text-natural-500">{rarity.icon} {rarity.label}</div>
                  </div>
                {/each}
              </div>
            </div>
          {/if}
          
          {#if getTopAchievements().length > 0}
            <div class="card p-6">
              <h2 class="section-title">✨ 高光成就</h2>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {#each getTopAchievements() as ua}
                  <AchievementCard achievement={ua} showShare={false} />
                {/each}
              </div>
            </div>
          {/if}
        </div>
        
        <div class="space-y-6">
          <div class="card p-6">
            <h3 class="font-bold text-natural-800 mb-4">🎯 近期活动</h3>
            <div class="space-y-4">
              {#if stats?.recent_corners && stats.recent_corners.length > 0}
                {#each stats.recent_corners.slice(0, 5) as corner}
                  <div class="flex items-start gap-3 p-3 rounded-xl hover:bg-natural-50 transition-colors">
                    <div class="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center flex-shrink-0">
                      📍
                    </div>
                    <div class="flex-1 min-w-0">
                      <p class="font-medium text-natural-800 truncate">{corner.title}</p>
                      <p class="text-xs text-natural-500">
                        发布于 {new Date(corner.created_at).toLocaleDateString('zh-CN')}
                      </p>
                    </div>
                  </div>
                {/each}
              {:else}
                <p class="text-natural-500 text-center py-4">暂无活动记录</p>
              {/if}
            </div>
          </div>
          
          <div class="card p-6">
            <h3 class="font-bold text-natural-800 mb-4">📊 成就点数分布</h3>
            <div class="space-y-4">
              {#each rarityFilters.slice(1) as rarity}
                {@const count = rarityCounts[rarity.value]}
                {@const points = count * (getRarityInfo(rarity.value)?.points || 0)}
                {@const totalPoints = achievementStats?.total_points || 1}
                {@const width = (points / totalPoints) * 100}
                <div class="flex items-center gap-3">
                  <span class="text-xl w-6">{rarity.icon}</span>
                  <div class="flex-1">
                    <div class="flex items-center justify-between text-sm mb-1">
                      <span class="text-natural-600">{rarity.label}</span>
                      <span class="font-medium" style="color: {rarity.color}">{points} 点</span>
                    </div>
                    <div class="h-2 bg-natural-100 rounded-full overflow-hidden">
                      <div
                        class="h-full rounded-full transition-all duration-500"
                        style="width: {width}%; background: {rarity.color}"
                      />
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        </div>
      </div>
    {/if}
    
    {#if activeTab === 'achievements'}
      <div class="space-y-6">
        <div class="flex flex-wrap gap-2 mb-6">
          {#each rarityFilters as rarity}
            <button
              on:click={() => rarityFilter = rarity.value}
              class="px-3 py-1.5 rounded-full text-sm font-medium transition-all flex items-center gap-1.5 {rarityFilter === rarity.value
                ? 'text-white shadow-soft'
                : 'bg-white text-natural-600 hover:bg-natural-50 border border-natural-200'}"
              style={rarityFilter === rarity.value ? `background: ${rarity.color}` : ''}
            >
              {#if rarity.icon}
                <span>{rarity.icon}</span>
              {/if}
              <span>{rarity.label}</span>
              <span class="text-xs opacity-80">
                ({rarity.value === 'all' ? unlockedCount : rarityCounts[rarity.value]})
              </span>
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
              {rarityFilter === 'all'
                ? '还没有解锁任何成就，快去探索吧！'
                : `还没有解锁${rarityFilters.find(r => r.value === rarityFilter)?.label}成就`}
            </p>
            {#if rarityFilter !== 'all'}
              <button on:click={() => rarityFilter = 'all'} class="btn btn-primary">
                查看全部成就
              </button>
            {/if}
          </div>
        {/if}
      </div>
    {/if}
    
    {#if activeTab === 'settings'}
      <div class="card p-6">
        <h2 class="section-title">⚙️ 个人设置</h2>
        
        {#if editing}
          <div class="max-w-lg space-y-6">
            <div>
              <label class="label">头像</label>
              <div class="flex items-center gap-4">
                <img
                  src={formData.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${formData.username}`}
                  alt="头像预览"
                  class="w-20 h-20 rounded-xl object-cover border-2 border-natural-200"
                />
                <div class="flex-1">
                  <input
                    type="text"
                    bind:value={formData.avatar}
                    class="input"
                    placeholder="头像URL"
                  />
                </div>
              </div>
            </div>
            
            <div>
              <label class="label">用户名</label>
              <input type="text" bind:value={formData.username} class="input" />
            </div>
            
            <div>
              <label class="label">邮箱</label>
              <input type="email" bind:value={formData.email} class="input" />
            </div>
            
            <div>
              <label class="label">个人简介</label>
              <textarea
                bind:value={formData.bio}
                class="input min-h-[120px]"
                placeholder="介绍一下自己..."
              />
            </div>
            
            <div class="flex gap-3">
              <button on:click={saveProfile} class="btn btn-primary">
                保存修改
              </button>
              <button on:click={() => editing = false} class="btn btn-outline">
                取消
              </button>
            </div>
          </div>
        {:else}
          <div class="max-w-lg space-y-6">
            <div class="flex items-center gap-4">
              <span class="text-natural-500 w-24">头像</span>
              <img
                src={$auth.user?.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${$auth.user?.username}`}
                alt="头像"
                class="w-16 h-16 rounded-xl object-cover border-2 border-natural-200"
              />
            </div>
            
            <div class="flex items-center gap-4">
              <span class="text-natural-500 w-24">用户名</span>
              <span class="font-medium text-natural-800">{$auth.user?.username}</span>
            </div>
            
            <div class="flex items-center gap-4">
              <span class="text-natural-500 w-24">邮箱</span>
              <span class="font-medium text-natural-800">{$auth.user?.email}</span>
            </div>
            
            <div class="flex items-start gap-4">
              <span class="text-natural-500 w-24">个人简介</span>
              <span class="text-natural-700">{$auth.user?.bio || '暂无简介'}</span>
            </div>
            
            <button on:click={() => editing = true} class="btn btn-primary">
              ✏️ 编辑资料
            </button>
          </div>
        {/if}
      </div>
    {/if}
  {/if}
</div>

<AchievementUnlockModal
  bind:isOpen={unlockModalOpen}
  bind:achievement={currentUnlockAchievement}
/>
