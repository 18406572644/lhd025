<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { cornerStore } from '$lib/stores/corners';
  import { auth } from '$lib/stores/auth';
  import { getUserStats } from '$lib/api/auth';
  import CornerCard from '$lib/components/CornerCard.svelte';
  import Loading from '$lib/components/Loading.svelte';
  import { toast } from '$lib/stores/toast';

  let corners = [];
  let loading = true;
  let searchQuery = '';
  let selectedCategory = '';
  let selectedDifficulty = '';
  let checkedInCorners = [];

  const categories = ['全部', '人文古迹', '自然风光', '文艺空间', '艺术创意', '体验工坊', '美食探店'];
  const difficulties = [
    { value: '', label: '全部难度' },
    { value: 'easy', label: '简单' },
    { value: 'medium', label: '中等' },
    { value: 'hard', label: '困难' }
  ];

  $: if ($page.url.searchParams.get('category')) {
    selectedCategory = $page.url.searchParams.get('category');
  }

  onMount(async () => {
    await loadCorners();
    if ($auth.isAuthenticated) {
      const stats = await getUserStats();
      checkedInCorners = stats?.checkin_corners || [];
    }
  });

  async function loadCorners() {
    loading = true;
    try {
      const params = {};
      if (selectedCategory && selectedCategory !== '全部') {
        params.category = selectedCategory;
      }
      if (selectedDifficulty) {
        params.difficulty = selectedDifficulty;
      }
      if (searchQuery) {
        params.search = searchQuery;
      }

      const data = await cornerStore.fetchCorners(params);
      if (data) {
        corners = data;
      }
    } catch (error) {
      toast.error('加载角落列表失败');
    } finally {
      loading = false;
    }
  }

  function handleSearch() {
    loadCorners();
  }

  function handleCategorySelect(category) {
    selectedCategory = category;
    loadCorners();
  }

  function handleDifficultyChange(e) {
    selectedDifficulty = e.target.value;
    loadCorners();
  }

  $: if (selectedCategory || selectedDifficulty) {
    // 响应式过滤
  }
</script>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-natural-800 mb-2">发现角落</h1>
    <p class="text-natural-600">探索城市中隐藏的美好，发现不一样的风景</p>
  </div>

  <!-- Search and Filters -->
  <div class="card p-6 mb-8">
    <div class="flex flex-col lg:flex-row gap-4">
      <div class="flex-1 relative">
        <input
          type="text"
          bind:value={searchQuery}
          on:keyup={(e) => e.key === 'Enter' && handleSearch()}
          class="input pr-12"
          placeholder="搜索角落名称、描述或标签..."
        />
        <button
          on:click={handleSearch}
          class="absolute right-3 top-1/2 -translate-y-1/2 text-primary-500 hover:text-primary-600"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
        </button>
      </div>
      
      <div class="w-full lg:w-48">
        <select on:change={handleDifficultyChange} class="input">
          {#each difficulties as diff}
            <option value={diff.value}>{diff.label}</option>
          {/each}
        </select>
      </div>
    </div>

    <!-- Category Tabs -->
    <div class="flex flex-wrap gap-2 mt-4">
      {#each categories as cat}
        <button
          on:click={() => handleCategorySelect(cat)}
          class="px-4 py-2 rounded-full text-sm font-medium transition-all {selectedCategory === cat || (cat === '全部' && !selectedCategory)
            ? 'bg-primary-500 text-white shadow-soft'
            : 'bg-natural-100 text-natural-600 hover:bg-primary-100 hover:text-primary-600'}"
        >
          {cat}
        </button>
      {/each}
    </div>
  </div>

  {#if loading}
    <Loading text="正在探索更多角落..." />
  {:else if corners.length > 0}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {#each corners as corner}
        <CornerCard
          {corner}
          showCheckinStatus={$auth.isAuthenticated}
          isCheckedIn={checkedInCorners.includes(corner.id)}
        />
      {/each}
    </div>
  {:else}
    <div class="card p-12 text-center">
      <div class="text-5xl mb-4">🔍</div>
      <p class="text-natural-600 mb-4">没有找到符合条件的角落</p>
      <button on:click={() => { selectedCategory = ''; selectedDifficulty = ''; searchQuery = ''; loadCorners(); }} class="btn btn-primary">
        清除筛选
      </button>
    </div>
  {/if}
</div>
