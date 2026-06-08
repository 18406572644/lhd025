<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { auth } from '$lib/stores/auth';
  import { cornerStore } from '$lib/stores/corners';
  import { getRoutes, createRoute, deleteRoute, recommendRoute } from '$lib/api/routes';
  import MapView from '$lib/components/MapView.svelte';
  import Loading from '$lib/components/Loading.svelte';
  import { toast } from '$lib/stores/toast';

  let routes = [];
  let corners = [];
  let loading = true;
  let creatingRoute = false;
  let deletingRouteId = null;

  let showCreateForm = false;
  let title = '';
  let description = '';
  let estimatedTime = '';
  let distance = '';
  let selectedCornerIds = [];
  let mapMarkers = [];
  let selectedRoute = null;
  let routeMapMarkers = [];

  let showRecommendModal = false;
  let recommendingRoute = false;
  let recommendResult = null;
  let recommendStartType = 'current';
  let recommendStartCornerId = null;
  let recommendCornerCount = 3;
  let recommendCategory = '';
  let recommendDifficulty = '';
  let currentLat = null;
  let currentLng = null;
  let recommendMapMarkers = [];
  let savingRecommendRoute = false;

  const categories = ['', '人文古迹', '自然风光', '文艺空间', '艺术创意', '体验工坊', '美食探店', '其他'];
  const difficulties = [
    { value: '', label: '全部难度' },
    { value: 'easy', label: '简单' },
    { value: 'medium', label: '中等' },
    { value: 'hard', label: '困难' }
  ];

  onMount(async () => {
    if (!$auth.isAuthenticated) {
      toast.warning('请先登录');
      goto('/login');
      return;
    }
    await loadData();
  });

  async function loadData() {
    loading = true;
    try {
      const [routesData, cornersData] = await Promise.all([
        getRoutes(),
        cornerStore.fetchCorners()
      ]);
      routes = routesData || [];
      corners = cornersData || [];
    } catch (error) {
      toast.error('加载数据失败');
    } finally {
      loading = false;
    }
  }

  function toggleCornerSelection(cornerId) {
    const index = selectedCornerIds.indexOf(cornerId);
    if (index > -1) {
      selectedCornerIds.splice(index, 1);
    } else {
      selectedCornerIds.push(cornerId);
    }
    updateFormMapMarkers();
  }

  function updateFormMapMarkers() {
    mapMarkers = selectedCornerIds.map((id, index) => {
      const corner = corners.find(c => c.id === id);
      if (!corner) return null;
      return {
        latitude: corner.latitude,
        longitude: corner.longitude,
        title: `${index + 1}. ${corner.title}`,
        content: corner.description.substring(0, 50) + '...',
        color: getRouteColor(index)
      };
    }).filter(Boolean);
  }

  function getRouteColor(index) {
    const colors = ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316'];
    return colors[index % colors.length];
  }

  async function handleCreateRoute(e) {
    e.preventDefault();
    
    if (!title || !description || selectedCornerIds.length < 2) {
      toast.error('请填写完整信息，至少选择2个角落');
      return;
    }

    creatingRoute = true;
    try {
      const routeData = {
        title,
        description,
        estimated_time: estimatedTime ? parseInt(estimatedTime) : null,
        distance: distance ? parseFloat(distance) : null,
        corner_ids: selectedCornerIds
      };

      await createRoute(routeData);
      toast.success('路线创建成功！');
      resetForm();
      await loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || '创建路线失败');
    } finally {
      creatingRoute = false;
    }
  }

  function resetForm() {
    showCreateForm = false;
    title = '';
    description = '';
    estimatedTime = '';
    distance = '';
    selectedCornerIds = [];
    mapMarkers = [];
  }

  function selectRoute(route) {
    selectedRoute = selectedRoute?.id === route.id ? null : route;
    if (selectedRoute) {
      updateRouteMapMarkers(selectedRoute);
    }
  }

  function updateRouteMapMarkers(route) {
    routeMapMarkers = route.corners.map((corner, index) => ({
      latitude: corner.latitude,
      longitude: corner.longitude,
      title: `${index + 1}. ${corner.title}`,
      content: corner.description.substring(0, 50) + '...',
      color: getRouteColor(index)
    }));
  }

  async function handleDeleteRoute(routeId, e) {
    e.stopPropagation();
    
    if (!confirm('确定要删除这条路线吗？')) return;

    deletingRouteId = routeId;
    try {
      await deleteRoute(routeId);
      toast.success('路线删除成功');
      if (selectedRoute?.id === routeId) {
        selectedRoute = null;
      }
      await loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || '删除路线失败');
    } finally {
      deletingRouteId = null;
    }
  }

  function getCornerById(id) {
    return corners.find(c => c.id === id);
  }

  function getCurrentLocation() {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          currentLat = position.coords.latitude;
          currentLng = position.coords.longitude;
          toast.success('已获取当前位置');
        },
        (error) => {
          toast.error('获取位置失败，请选择指定角落作为起点');
          recommendStartType = 'corner';
        }
      );
    } else {
      toast.error('浏览器不支持定位功能');
      recommendStartType = 'corner';
    }
  }

  function updateRecommendMapMarkers(result) {
    recommendMapMarkers = result.corners.map((corner, index) => ({
      latitude: corner.latitude,
      longitude: corner.longitude,
      title: `${index + 1}. ${corner.title}`,
      content: corner.description.substring(0, 50) + '...',
      color: getRouteColor(index)
    }));
  }

  async function handleRecommendRoute(e) {
    e.preventDefault();

    if (recommendStartType === 'current') {
      if (!currentLat || !currentLng) {
        toast.error('请先获取当前位置');
        return;
      }
    } else {
      if (!recommendStartCornerId) {
        toast.error('请选择起点角落');
        return;
      }
    }

    recommendingRoute = true;
    try {
      const requestData = {
        corner_count: recommendCornerCount
      };

      if (recommendStartType === 'current') {
        requestData.start_lat = currentLat;
        requestData.start_lng = currentLng;
      } else {
        requestData.start_corner_id = recommendStartCornerId;
      }

      if (recommendCategory) {
        requestData.category = recommendCategory;
      }
      if (recommendDifficulty) {
        requestData.difficulty = recommendDifficulty;
      }

      const result = await recommendRoute(requestData);
      recommendResult = result;
      updateRecommendMapMarkers(result);
      toast.success('路线推荐成功！');
    } catch (error) {
      toast.error(error.response?.data?.detail || '路线推荐失败');
    } finally {
      recommendingRoute = false;
    }
  }

  async function handleSaveRecommendRoute() {
    if (!recommendResult) return;

    if (!title || !description) {
      toast.error('请填写路线标题和描述');
      return;
    }

    const validCornerIds = recommendResult.corners
      .filter(c => c.id > 0)
      .map(c => c.id);

    if (validCornerIds.length < 2) {
      toast.error('推荐路线中有效角落不足');
      return;
    }

    savingRecommendRoute = true;
    try {
      const routeData = {
        title,
        description,
        estimated_time: recommendResult.estimated_time,
        distance: recommendResult.total_distance,
        corner_ids: validCornerIds
      };

      await createRoute(routeData);
      toast.success('路线保存成功！');
      closeRecommendModal();
      await loadData();
    } catch (error) {
      toast.error(error.response?.data?.detail || '保存路线失败');
    } finally {
      savingRecommendRoute = false;
    }
  }

  function closeRecommendModal() {
    showRecommendModal = false;
    recommendResult = null;
    recommendMapMarkers = [];
    title = '';
    description = '';
  }

  function openRecommendModal() {
    showRecommendModal = true;
    recommendResult = null;
    recommendStartType = 'current';
    recommendCornerCount = 3;
    recommendCategory = '';
    recommendDifficulty = '';
    recommendStartCornerId = null;
    currentLat = null;
    currentLng = null;
    getCurrentLocation();
  }

  $: if (selectedCornerIds.length > 0 && corners.length > 0) {
    updateFormMapMarkers();
  }
</script>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-natural-800 mb-2">路线规划</h1>
    <p class="text-natural-600">规划你的城市探索路线，串联起多个美好的角落</p>
  </div>

  {#if loading}
    <Loading text="正在加载路线数据..." />
  {:else}
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left Panel: Routes List & Create Form -->
      <div class="lg:col-span-1 space-y-6">
        <!-- Create Route Button/Form -->
        {#if !showCreateForm}
          <div class="space-y-3">
            <button
              on:click={() => showCreateForm = true}
              class="w-full btn btn-primary py-4 text-lg flex items-center justify-center gap-2"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
              </svg>
              创建新路线
            </button>
            <button
              on:click={openRecommendModal}
              class="w-full btn btn-secondary py-4 text-lg flex items-center justify-center gap-2"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
              </svg>
              智能推荐路线
            </button>
          </div>
        {:else}
          <div class="card p-6">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-xl font-bold text-natural-800">📝 创建路线</h2>
              <button on:click={resetForm} class="text-natural-500 hover:text-natural-700">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>

            <form on:submit={handleCreateRoute} class="space-y-4">
              <div>
                <label class="label">路线标题 *</label>
                <input
                  type="text"
                  bind:value={title}
                  class="input"
                  placeholder="给这条路线起个名字"
                  maxlength="100"
                />
              </div>

              <div>
                <label class="label">路线描述 *</label>
                <textarea
                  bind:value={description}
                  class="input min-h-[100px] resize-none"
                  placeholder="描述这条路线的特色和亮点..."
                  maxlength="500"
                ></textarea>
              </div>

              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="label">预计时间（分钟）</label>
                  <input
                    type="number"
                    bind:value={estimatedTime}
                    class="input"
                    placeholder="例如：120"
                    min="1"
                  />
                </div>
                <div>
                  <label class="label">距离（公里）</label>
                  <input
                    type="number"
                    step="0.1"
                    bind:value={distance}
                    class="input"
                    placeholder="例如：5.0"
                    min="0.1"
                  />
                </div>
              </div>

              <div>
                <label class="label">选择角落 *（至少2个）</label>
                <div class="max-h-60 overflow-y-auto space-y-2 border-2 border-natural-200 rounded-xl p-3">
                  {#if corners.length === 0}
                    <p class="text-natural-500 text-center py-4">暂无可用角落</p>
                  {:else}
                    {#each corners as corner}
                      <label
                        class="flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all {selectedCornerIds.includes(corner.id)
                          ? 'bg-primary-100 border-2 border-primary-400'
                          : 'bg-natural-50 border-2 border-transparent hover:bg-natural-100'}"
                      >
                        <input
                          type="checkbox"
                          checked={selectedCornerIds.includes(corner.id)}
                          on:change={() => toggleCornerSelection(corner.id)}
                          class="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                        />
                        <div class="flex-1 min-w-0">
                          <p class="font-medium text-natural-800 truncate">{corner.title}</p>
                          <p class="text-xs text-natural-500 truncate">{corner.address || corner.category}</p>
                        </div>
                      </label>
                    {/each}
                  {/if}
                </div>
                <p class="text-sm text-natural-500 mt-2">
                  已选择 {selectedCornerIds.length} 个角落
                </p>
              </div>

              <div class="flex gap-3 pt-2">
                <button
                  type="button"
                  on:click={resetForm}
                  class="btn btn-outline flex-1"
                >
                  取消
                </button>
                <button
                  type="submit"
                  class="btn btn-primary flex-1"
                  disabled={creatingRoute}
                >
                  {#if creatingRoute}
                    <span class="inline-flex items-center gap-2">
                      <span class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                      创建中...
                    </span>
                  {:else}
                    创建路线
                  {/if}
                </button>
              </div>
            </form>
          </div>
        {/if}

        <!-- Routes List -->
        <div class="card p-6">
          <h2 class="text-xl font-bold text-natural-800 mb-4">🗺️ 我的路线</h2>
          
          {#if routes.length === 0}
            <div class="text-center py-8">
              <div class="text-4xl mb-3">🛤️</div>
              <p class="text-natural-600 mb-4">还没有创建路线</p>
              {#if !showCreateForm}
                <button on:click={() => showCreateForm = true} class="btn btn-secondary text-sm">
                  创建第一条路线
                </button>
              {/if}
            </div>
          {:else}
            <div class="space-y-3 max-h-[500px] overflow-y-auto">
              {#each routes as route}
                <div
                  on:click={() => selectRoute(route)}
                  class="p-4 rounded-xl cursor-pointer transition-all border-2 {selectedRoute?.id === route.id
                    ? 'border-primary-400 bg-primary-50'
                    : 'border-transparent bg-natural-50 hover:bg-natural-100'}"
                >
                  <div class="flex items-start justify-between gap-2">
                    <div class="flex-1 min-w-0">
                      <h3 class="font-semibold text-natural-800 truncate">{route.title}</h3>
                      <p class="text-sm text-natural-500 mt-1 line-clamp-2">{route.description}</p>
                      <div class="flex flex-wrap gap-2 mt-2">
                        {#if route.estimated_time}
                          <span class="badge badge-primary">
                            ⏱️ {route.estimated_time}分钟
                          </span>
                        {/if}
                        {#if route.distance}
                          <span class="badge badge-secondary">
                            📏 {route.distance}km
                          </span>
                        {/if}
                        <span class="badge bg-natural-100 text-natural-700">
                          📍 {route.corners?.length || 0}个角落
                        </span>
                      </div>
                    </div>
                    <button
                      on:click={(e) => handleDeleteRoute(route.id, e)}
                      class="p-2 text-red-500 hover:bg-red-100 rounded-lg transition-colors"
                      disabled={deletingRouteId === route.id}
                      title="删除路线"
                    >
                      {#if deletingRouteId === route.id}
                        <span class="w-5 h-5 border-2 border-red-300 border-t-red-500 rounded-full animate-spin inline-block"></span>
                      {:else}
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                        </svg>
                      {/if}
                    </button>
                  </div>

                  {#if selectedRoute?.id === route.id && route.corners?.length > 0}
                    <div class="mt-3 pt-3 border-t border-natural-200">
                      <p class="text-xs font-medium text-natural-600 mb-2">路线途经：</p>
                      <div class="flex flex-wrap gap-1">
                        {#each route.corners as corner, index}
                          <span
                            class="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium"
                            style="background-color: {getRouteColor(index)}20; color: {getRouteColor(index)};"
                          >
                            <span class="w-4 h-4 rounded-full text-white text-center flex items-center justify-center text-xs" style="background-color: {getRouteColor(index)};">
                              {index + 1}
                            </span>
                            {corner.title}
                          </span>
                        {/each}
                      </div>
                    </div>
                  {/if}
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>

      <!-- Right Panel: Map -->
      <div class="lg:col-span-2">
        <div class="card p-6 h-full">
          <h2 class="text-xl font-bold text-natural-800 mb-4">
            {#if showCreateForm}
              📍 路线预览
            {:else if selectedRoute}
              🗺️ {selectedRoute.title}
            {:else}
              🗺️ 路线地图
            {/if}
          </h2>

          <div class="h-96 lg:h-[calc(100vh-300px)] min-h-[400px]">
            {#if showCreateForm && mapMarkers.length > 0}
              <MapView
                markers={mapMarkers}
                center={[mapMarkers[0].latitude, mapMarkers[0].longitude]}
                zoom={12}
              />
            {:else if selectedRoute && routeMapMarkers.length > 0}
              <MapView
                markers={routeMapMarkers}
                center={[routeMapMarkers[0].latitude, routeMapMarkers[0].longitude]}
                zoom={12}
              />
            {:else if selectedRoute && routeMapMarkers.length === 0}
              <div class="h-full flex items-center justify-center bg-natural-50 rounded-xl">
                <div class="text-center">
                  <div class="text-4xl mb-3">📍</div>
                  <p class="text-natural-500">该路线暂无位置数据</p>
                </div>
              </div>
            {:else if showCreateForm}
              <div class="h-full flex items-center justify-center bg-natural-50 rounded-xl">
                <div class="text-center">
                  <div class="text-4xl mb-3">👆</div>
                  <p class="text-natural-600 mb-2">选择角落来预览路线</p>
                  <p class="text-sm text-natural-500">在左侧表单中选择至少2个角落</p>
                </div>
              </div>
            {:else}
              <div class="h-full flex items-center justify-center bg-natural-50 rounded-xl">
                <div class="text-center">
                  <div class="text-4xl mb-3">🗺️</div>
                  <p class="text-natural-600 mb-2">选择一条路线查看地图</p>
                  <p class="text-sm text-natural-500">或创建一条新的探索路线</p>
                </div>
              </div>
            {/if}
          </div>

          {#if selectedRoute && selectedRoute.corners?.length > 0}
            <div class="mt-4 pt-4 border-t border-natural-200">
              <h3 class="font-semibold text-natural-800 mb-3">📋 路线详情</h3>
              <div class="space-y-3">
                {#each selectedRoute.corners as corner, index}
                  <div class="flex items-start gap-3 p-3 bg-natural-50 rounded-xl">
                    <span
                      class="w-6 h-6 rounded-full text-white text-sm font-bold flex items-center justify-center flex-shrink-0"
                      style="background-color: {getRouteColor(index)};"
                    >
                      {index + 1}
                    </span>
                    <div class="flex-1 min-w-0">
                      <p class="font-medium text-natural-800">{corner.title}</p>
                      <p class="text-sm text-natural-500 mt-1">{corner.description}</p>
                      {#if corner.address}
                        <p class="text-xs text-natural-400 mt-1">📍 {corner.address}</p>
                      {/if}
                    </div>
                  </div>
                {/each}
              </div>
            </div>
          {/if}
        </div>
      </div>
    </div>
  {/if}
</div>

<!-- Recommend Route Modal -->
{#if showRecommendModal}
  <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" on:click|self={closeRecommendModal}>
    <div class="bg-white rounded-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
      <div class="p-6 border-b border-natural-200 flex items-center justify-between">
        <h2 class="text-2xl font-bold text-natural-800">🧠 智能路线推荐</h2>
        <button on:click={closeRecommendModal} class="text-natural-500 hover:text-natural-700 p-2">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <div class="flex-1 overflow-y-auto">
        {#if !recommendResult}
          <div class="p-6">
            <form on:submit={handleRecommendRoute} class="space-y-6">
              <div>
                <label class="label">选择起点</label>
                <div class="grid grid-cols-2 gap-4">
                  <label class="flex items-center gap-3 p-4 rounded-xl cursor-pointer transition-all border-2 {recommendStartType === 'current'
                    ? 'bg-primary-50 border-primary-400'
                    : 'bg-natural-50 border-transparent hover:bg-natural-100'}">
                    <input
                      type="radio"
                      bind:group={recommendStartType}
                      value="current"
                      class="w-4 h-4 text-primary-600"
                    />
                    <div>
                      <p class="font-medium text-natural-800">📍 当前位置</p>
                      {#if currentLat && currentLng}
                        <p class="text-xs text-natural-500">
                          {currentLat.toFixed(4)}, {currentLng.toFixed(4)}
                        </p>
                      {:else}
                        <p class="text-xs text-natural-400">正在获取位置...</p>
                      {/if}
                    </div>
                  </label>
                  <label class="flex items-center gap-3 p-4 rounded-xl cursor-pointer transition-all border-2 {recommendStartType === 'corner'
                    ? 'bg-primary-50 border-primary-400'
                    : 'bg-natural-50 border-transparent hover:bg-natural-100'}">
                    <input
                      type="radio"
                      bind:group={recommendStartType}
                      value="corner"
                      class="w-4 h-4 text-primary-600"
                    />
                    <div>
                      <p class="font-medium text-natural-800">🏛️ 指定角落</p>
                      <p class="text-xs text-natural-500">选择一个角落作为起点</p>
                    </div>
                  </label>
                </div>
              </div>

              {#if recommendStartType === 'corner'}
                <div>
                  <label class="label">选择起点角落</label>
                  <select bind:value={recommendStartCornerId} class="input">
                    <option value={null}>请选择起点角落</option>
                    {#each corners as corner}
                      <option value={corner.id}>{corner.title}</option>
                    {/each}
                  </select>
                </div>
              {:else}
                <button
                  type="button"
                  on:click={getCurrentLocation}
                  class="btn btn-secondary text-sm"
                >
                  🔄 重新获取位置
                </button>
              {/if}

              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="label">探访角落数量</label>
                  <select bind:value={recommendCornerCount} class="input">
                    {#each [2, 3, 4, 5, 6, 7, 8, 9, 10] as count}
                      <option value={count}>{count} 个</option>
                    {/each}
                  </select>
                </div>
                <div>
                  <label class="label">分类筛选</label>
                  <select bind:value={recommendCategory} class="input">
                    {#each categories as cat}
                      <option value={cat}>{cat || '全部分类'}</option>
                    {/each}
                  </select>
                </div>
              </div>

              <div>
                <label class="label">难度筛选</label>
                <div class="flex flex-wrap gap-2">
                  {#each difficulties as diff}
                    <label class="inline-flex items-center gap-2 px-4 py-2 rounded-lg cursor-pointer transition-all border-2 {recommendDifficulty === diff.value
                      ? 'bg-primary-50 border-primary-400'
                      : 'bg-natural-50 border-transparent hover:bg-natural-100'}">
                      <input
                        type="radio"
                        bind:group={recommendDifficulty}
                        value={diff.value}
                        class="w-4 h-4 text-primary-600"
                      />
                      <span class="text-sm">{diff.label}</span>
                    </label>
                  {/each}
                </div>
              </div>

              <button
                type="submit"
                class="w-full btn btn-primary py-4 text-lg"
                disabled={recommendingRoute}
              >
                {#if recommendingRoute}
                  <span class="inline-flex items-center gap-2">
                    <span class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                    智能计算中...
                  </span>
                {:else}
                  ✨ 开始推荐
                {/if}
              </button>
            </form>
          </div>
        {:else}
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-0 h-full">
            <div class="p-6 border-r border-natural-200 overflow-y-auto">
              <div class="mb-6">
                <div class="flex items-center gap-3 mb-4">
                  <span class="text-3xl">🎉</span>
                  <div>
                    <h3 class="text-xl font-bold text-natural-800">推荐成功！</h3>
                    <p class="text-natural-500">已为您计算最优游览路线</p>
                  </div>
                </div>
                <div class="grid grid-cols-3 gap-4">
                  <div class="bg-primary-50 rounded-xl p-4 text-center">
                    <p class="text-2xl font-bold text-primary-600">{recommendResult.total_distance}</p>
                    <p class="text-sm text-natural-600">公里</p>
                  </div>
                  <div class="bg-secondary-50 rounded-xl p-4 text-center">
                    <p class="text-2xl font-bold text-secondary-600">{recommendResult.estimated_time}</p>
                    <p class="text-sm text-natural-600">分钟</p>
                  </div>
                  <div class="bg-natural-100 rounded-xl p-4 text-center">
                    <p class="text-2xl font-bold text-natural-600">{recommendResult.corners.length}</p>
                    <p class="text-sm text-natural-600">个地点</p>
                  </div>
                </div>
              </div>

              <div class="space-y-3">
                <h4 class="font-semibold text-natural-800">📍 路线详情</h4>
                {#each recommendResult.corners as corner, index}
                  <div class="flex items-start gap-3 p-4 bg-natural-50 rounded-xl">
                    <span
                      class="w-8 h-8 rounded-full text-white text-sm font-bold flex items-center justify-center flex-shrink-0"
                      style="background-color: {getRouteColor(index)};"
                    >
                      {index + 1}
                    </span>
                    <div class="flex-1 min-w-0">
                      <p class="font-medium text-natural-800">{corner.title}</p>
                      <p class="text-sm text-natural-500 mt-1 line-clamp-2">{corner.description}</p>
                      {#if corner.category}
                        <span class="inline-block mt-2 text-xs bg-primary-100 text-primary-700 px-2 py-1 rounded">
                          {corner.category}
                        </span>
                      {/if}
                      {#if index < recommendResult.distances.length}
                        <p class="text-xs text-natural-400 mt-2">
                          → 下一站 {recommendResult.distances[index]} km
                        </p>
                      {/if}
                    </div>
                  </div>
                {/each}
              </div>

              <div class="mt-6 pt-6 border-t border-natural-200">
                <h4 class="font-semibold text-natural-800 mb-3">💾 保存路线</h4>
                <div class="space-y-3">
                  <div>
                    <label class="label">路线标题 *</label>
                    <input
                      type="text"
                      bind:value={title}
                      class="input"
                      placeholder="给这条路线起个名字"
                      maxlength="100"
                    />
                  </div>
                  <div>
                    <label class="label">路线描述 *</label>
                    <textarea
                      bind:value={description}
                      class="input min-h-[80px] resize-none"
                      placeholder="描述这条路线的特色..."
                      maxlength="500"
                    ></textarea>
                  </div>
                  <button
                    on:click={handleSaveRecommendRoute}
                    class="w-full btn btn-primary py-3"
                    disabled={savingRecommendRoute}
                  >
                    {#if savingRecommendRoute}
                      <span class="inline-flex items-center gap-2">
                        <span class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                        保存中...
                      </span>
                    {:else}
                      ✅ 保存为我的路线
                    {/if}
                  </button>
                  <button
                    type="button"
                    on:click={() => recommendResult = null}
                    class="w-full btn btn-outline py-3"
                  >
                    🔄 重新推荐
                  </button>
                </div>
              </div>
            </div>

            <div class="p-6">
              <h4 class="font-semibold text-natural-800 mb-4">🗺️ 路线地图</h4>
              <div class="h-[calc(90vh-180px)] min-h-[400px]">
                {#if recommendMapMarkers.length > 0}
                  <MapView
                    markers={recommendMapMarkers}
                    center={[recommendMapMarkers[0].latitude, recommendMapMarkers[0].longitude]}
                    zoom={12}
                  />
                {:else}
                  <div class="h-full flex items-center justify-center bg-natural-50 rounded-xl">
                    <div class="text-center">
                      <div class="text-4xl mb-3">📍</div>
                      <p class="text-natural-500">地图加载中...</p>
                    </div>
                  </div>
                {/if}
              </div>
            </div>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}
