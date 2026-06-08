<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { auth } from '$lib/stores/auth';
  import { cornerStore } from '$lib/stores/corners';
  import MapView from '$lib/components/MapView.svelte';
  import Loading from '$lib/components/Loading.svelte';
  import { toast } from '$lib/stores/toast';

  let title = '';
  let description = '';
  let category = '人文古迹';
  let latitude = 39.9042;
  let longitude = 116.4074;
  let address = '';
  let images = '';
  let tags = '';
  let difficulty = 'easy';
  let loading = false;
  let mapLoading = true;

  const categories = ['人文古迹', '自然风光', '文艺空间', '艺术创意', '体验工坊', '美食探店', '其他'];
  const difficulties = [
    { value: 'easy', label: '简单 - 轻松可达' },
    { value: 'medium', label: '中等 - 需要寻找' },
    { value: 'hard', label: '困难 - 隐秘角落' }
  ];

  let mapMarkers = [];

  onMount(() => {
    if (!$auth.isAuthenticated) {
      toast.warning('请先登录');
      goto('/login');
      return;
    }
    updateMapMarker();
    setTimeout(() => mapLoading = false, 500);
  });

  function handleMapClick(e) {
    const { latitude: lat, longitude: lng } = e.detail;
    latitude = lat;
    longitude = lng;
    updateMapMarker();
  }

  function updateMapMarker() {
    mapMarkers = [{
      latitude,
      longitude,
      title: title || '新角落位置',
      color: '#22c55e'
    }];
  }

  $: if (latitude && longitude) {
    updateMapMarker();
  }

  async function handleSubmit(e) {
    e.preventDefault();
    
    if (!title || !description || !category || !latitude || !longitude) {
      toast.error('请填写完整信息');
      return;
    }

    if (description.length < 10) {
      toast.error('描述至少需要10个字符');
      return;
    }

    loading = true;
    try {
      const result = await cornerStore.createCorner({
        title,
        description,
        category,
        latitude: parseFloat(latitude),
        longitude: parseFloat(longitude),
        address,
        images,
        tags,
        difficulty
      });

      if (result.success) {
        toast.success('角落发布成功！');
        goto(`/corners/${result.data.id}`);
      } else {
        toast.error(result.error);
      }
    } catch (error) {
      toast.error('发布失败，请重试');
    } finally {
      loading = false;
    }
  }

  function useCurrentLocation() {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          latitude = position.coords.latitude;
          longitude = position.coords.longitude;
          updateMapMarker();
          toast.success('已获取当前位置');
        },
        (error) => {
          toast.error('获取位置失败，请手动选择');
        }
      );
    } else {
      toast.error('浏览器不支持定位功能');
    }
  }
</script>

<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-natural-800 mb-2">发布新角落</h1>
    <p class="text-natural-600">分享你发现的城市秘密，让更多人感受到这些隐藏的美好</p>
  </div>

  <form on:submit={handleSubmit} class="space-y-6">
    <!-- Map Section -->
    <div class="card p-6">
      <h2 class="text-xl font-bold text-natural-800 mb-4">📍 选择位置</h2>
      <p class="text-natural-600 text-sm mb-4">点击地图选择角落位置，或使用当前位置</p>
      
      <div class="flex gap-3 mb-4">
        <button type="button" on:click={useCurrentLocation} class="btn btn-secondary text-sm">
          📍 使用当前位置
        </button>
      </div>

      <div class="h-80 relative">
        {#if mapLoading}
          <Loading text="地图加载中..." />
        {/if}
        <div class="{mapLoading ? 'opacity-0' : 'opacity-100'} transition-opacity h-full">
          <MapView
            markers={mapMarkers}
            center={[latitude, longitude]}
            zoom={13}
            clickable={true}
            on:mapClick={handleMapClick}
          />
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4 mt-4">
        <div>
          <label class="label">纬度</label>
          <input
            type="number"
            step="any"
            bind:value={latitude}
            class="input"
            placeholder="输入纬度"
          />
        </div>
        <div>
          <label class="label">经度</label>
          <input
            type="number"
            step="any"
            bind:value={longitude}
            class="input"
            placeholder="输入经度"
          />
        </div>
      </div>
    </div>

    <!-- Basic Info -->
    <div class="card p-6">
      <h2 class="text-xl font-bold text-natural-800 mb-4">📝 基本信息</h2>
      
      <div class="space-y-4">
        <div>
          <label class="label">角落名称 *</label>
          <input
            type="text"
            bind:value={title}
            class="input"
            placeholder="给这个角落起个好听的名字"
            maxlength="100"
          />
        </div>

        <div>
          <label class="label">详细描述 *</label>
          <textarea
            bind:value={description}
            class="input min-h-[150px] resize-none"
            placeholder="详细描述这个角落的特色、如何找到它、最佳探索时间等..."
            maxlength="2000"
          ></textarea>
          <p class="text-right text-sm text-natural-500 mt-1">{description.length}/2000</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="label">分类 *</label>
            <select bind:value={category} class="input">
              {#each categories as cat}
                <option value={cat}>{cat}</option>
              {/each}
            </select>
          </div>
          <div>
            <label class="label">探索难度</label>
            <select bind:value={difficulty} class="input">
              {#each difficulties as diff}
                <option value={diff.value}>{diff.label}</option>
              {/each}
            </select>
          </div>
        </div>

        <div>
          <label class="label">详细地址</label>
          <input
            type="text"
            bind:value={address}
            class="input"
            placeholder="例如：北京市东城区xx路xx号"
          />
        </div>

        <div>
          <label class="label">封面图片链接</label>
          <input
            type="url"
            bind:value={images}
            class="input"
            placeholder="https://example.com/image.jpg"
          />
          {#if images}
            <div class="mt-2 rounded-xl overflow-hidden">
              <img src={images} alt="预览" class="w-full h-48 object-cover" />
            </div>
          {/if}
        </div>

        <div>
          <label class="label">标签</label>
          <input
            type="text"
            bind:value={tags}
            class="input"
            placeholder="多个标签用逗号分隔，例如：复古,摄影,小众"
          />
          {#if tags}
            <div class="flex flex-wrap gap-2 mt-2">
              {#each tags.split(',').filter(t => t.trim()) as tag}
                <span class="text-xs bg-primary-100 text-primary-700 px-2 py-1 rounded-full">
                  #{tag.trim()}
                </span>
              {/each}
            </div>
          {/if}
        </div>
      </div>
    </div>

    <!-- Submit -->
    <div class="flex flex-col sm:flex-row gap-4 justify-end">
      <button type="button" on:click={() => history.back()} class="btn btn-outline">
        取消
      </button>
      <button type="submit" class="btn btn-primary px-8" disabled={loading}>
        {#if loading}
          <span class="inline-flex items-center gap-2">
            <span class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            发布中...
          </span>
        {:else}
          发布角落
        {/if}
      </button>
    </div>
  </form>
</div>
