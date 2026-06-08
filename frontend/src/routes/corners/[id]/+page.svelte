<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { cornerStore } from '$lib/stores/corners';
  import { checkinStore } from '$lib/stores/checkins';
  import { auth } from '$lib/stores/auth';
  import { getCheckins } from '$lib/api/checkins';
  import { createShare } from '$lib/api/shares';
  import MapView from '$lib/components/MapView.svelte';
  import Loading from '$lib/components/Loading.svelte';
  import { toast } from '$lib/stores/toast';

  let corner = null;
  let loading = true;
  let checkins = [];
  let isCheckedIn = false;
  let showCheckinModal = false;
  let checkinContent = '';
  let checkinRating = 5;
  let checkinLoading = false;

  const difficultyColors = {
    easy: 'badge-primary',
    medium: 'badge-warning',
    hard: 'badge-danger'
  };

  const difficultyLabels = {
    easy: '简单',
    medium: '中等',
    hard: '困难'
  };

  $: cornerId = $page.params.id;

  onMount(async () => {
    await loadCorner();
    await loadCheckins();
  });

  async function loadCorner() {
    loading = true;
    try {
      corner = await cornerStore.fetchCorner(cornerId);
    } catch (error) {
      toast.error('加载角落详情失败');
    } finally {
      loading = false;
    }
  }

  async function loadCheckins() {
    try {
      const data = await getCheckins({ corner_id: cornerId });
      if (data) {
        checkins = data;
        isCheckedIn = data.some(c => c.user_id === $auth.user?.id);
      }
    } catch (error) {
      console.error('Failed to load checkins');
    }
  }

  async function handleCheckin() {
    if (!$auth.isAuthenticated) {
      toast.warning('请先登录');
      goto('/login');
      return;
    }

    checkinLoading = true;
    try {
      const result = await checkinStore.createCheckin({
        corner_id: parseInt(cornerId),
        content: checkinContent,
        rating: checkinRating
      });

      if (result.success) {
        toast.success('打卡成功！');
        showCheckinModal = false;
        checkinContent = '';
        checkinRating = 5;
        await loadCheckins();
      } else {
        toast.error(result.error);
      }
    } catch (error) {
      toast.error('打卡失败');
    } finally {
      checkinLoading = false;
    }
  }

  async function handleShare(platform) {
    if (!$auth.isAuthenticated) {
      toast.warning('请先登录');
      goto('/login');
      return;
    }

    try {
      await createShare({
        content_type: 'corner',
        content_id: parseInt(cornerId),
        platform
      });

      const shareText = `我在「角落探索」发现了一个很棒的地方：${corner.title}！`;
      const shareUrl = window.location.href;

      if (platform === 'weixin') {
        toast.success('已复制分享链接，快去分享给微信好友吧！');
        navigator.clipboard.writeText(`${shareText} ${shareUrl}`);
      } else if (platform === 'weibo') {
        window.open(`https://service.weibo.com/share/share.php?title=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`);
      } else {
        navigator.clipboard.writeText(`${shareText} ${shareUrl}`);
        toast.success('分享链接已复制到剪贴板！');
      }
    } catch (error) {
      toast.error('分享失败');
    }
  }

  function getStars(rating) {
    return '⭐'.repeat(rating) + '☆'.repeat(5 - rating);
  }

  $: mapMarkers = corner ? [{
    latitude: corner.latitude,
    longitude: corner.longitude,
    title: corner.title,
    content: corner.address
  }] : [];
</script>

{#if loading}
  <Loading fullscreen text="正在加载角落详情..." />
{:else if corner}
  <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
    <!-- Header Image -->
    <div class="relative rounded-2xl overflow-hidden mb-8">
      <img
        src={corner.images || 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1200'}
        alt={corner.title}
        class="w-full h-64 md:h-96 object-cover"
      />
      <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent"></div>
      <div class="absolute bottom-0 left-0 right-0 p-6 md:p-8 text-white">
        <div class="flex flex-wrap items-center gap-3 mb-3">
          <span class="badge {difficultyColors[corner.difficulty]}">{difficultyLabels[corner.difficulty]}</span>
          <span class="badge bg-white/20 backdrop-blur-sm text-white border-none">{corner.category}</span>
          {#if isCheckedIn}
            <span class="badge bg-green-500 text-white">✅ 已打卡</span>
          {/if}
        </div>
        <h1 class="text-3xl md:text-4xl font-bold mb-2">{corner.title}</h1>
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2">
            <img
              src={corner.author?.avatar || 'https://api.dicebear.com/7.x/avataaars/svg?seed=default'}
              alt={corner.author?.username}
              class="w-8 h-8 rounded-full border-2 border-white/30"
            />
            <span>{corner.author?.username || '匿名用户'}</span>
          </div>
          <div class="flex items-center gap-1">
            <span>👥</span>
            <span>{corner.checkin_count || 0} 人打卡</span>
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Main Content -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Description -->
        <div class="card p-6">
          <h2 class="text-xl font-bold text-natural-800 mb-4">📝 角落介绍</h2>
          <p class="text-natural-600 leading-relaxed whitespace-pre-wrap">{corner.description}</p>
        </div>

        <!-- Tags -->
        {#if corner.tags}
          <div class="card p-6">
            <h2 class="text-xl font-bold text-natural-800 mb-4">🏷️ 标签</h2>
            <div class="flex flex-wrap gap-2">
              {#each corner.tags.split(',') as tag}
                <span class="text-sm bg-primary-50 text-primary-700 px-3 py-1 rounded-full">
                  #{tag.trim()}
                </span>
              {/each}
            </div>
          </div>
        {/if}

        <!-- Checkins -->
        <div class="card p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-xl font-bold text-natural-800">✅ 打卡记录 ({checkins.length})</h2>
            {#if $auth.isAuthenticated && !isCheckedIn}
              <button on:click={() => showCheckinModal = true} class="btn btn-primary text-sm">
                + 打卡
              </button>
            {/if}
          </div>

          {#if checkins.length > 0}
            <div class="space-y-4">
              {#each checkins as checkin}
                <div class="flex gap-4 p-4 bg-natural-50 rounded-xl">
                  <img
                    src={checkin.user?.avatar || 'https://api.dicebear.com/7.x/avataaars/svg?seed=default'}
                    alt={checkin.user?.username}
                    class="w-10 h-10 rounded-full flex-shrink-0"
                  />
                  <div class="flex-1">
                    <div class="flex items-center justify-between mb-1">
                      <span class="font-medium text-natural-800">{checkin.user?.username}</span>
                      <span class="text-sm text-natural-500">{new Date(checkin.created_at).toLocaleDateString()}</span>
                    </div>
                    <div class="text-yellow-500 text-sm mb-1">{getStars(checkin.rating)}</div>
                    {#if checkin.content}
                      <p class="text-natural-600 text-sm">{checkin.content}</p>
                    {/if}
                  </div>
                </div>
              {/each}
            </div>
          {:else}
            <div class="text-center py-8 text-natural-500">
              <div class="text-4xl mb-2">✍️</div>
              <p>还没有打卡记录，成为第一个打卡的人吧！</p>
            </div>
          {/if}
        </div>
      </div>

      <!-- Sidebar -->
      <div class="space-y-6">
        <!-- Location Map -->
        <div class="card p-6">
          <h2 class="text-xl font-bold text-natural-800 mb-4">📍 位置信息</h2>
          <div class="h-64 mb-4">
            <MapView
              markers={mapMarkers}
              center={[corner.latitude, corner.longitude]}
              zoom={15}
              interactive={false}
              showControls={false}
            />
          </div>
          <p class="text-natural-600 text-sm mb-2">
            <span class="font-medium">地址：</span>{corner.address || '暂无详细地址'}
          </p>
          <p class="text-natural-600 text-sm">
            <span class="font-medium">坐标：</span>{corner.latitude.toFixed(6)}, {corner.longitude.toFixed(6)}
          </p>
        </div>

        <!-- Actions -->
        <div class="card p-6">
          <h2 class="text-xl font-bold text-natural-800 mb-4">🎯 操作</h2>
          <div class="space-y-3">
            {#if $auth.isAuthenticated && !isCheckedIn}
              <button on:click={() => showCheckinModal = true} class="btn btn-primary w-full">
                ✅ 立即打卡
              </button>
            {:else if isCheckedIn}
              <button disabled class="btn bg-green-100 text-green-700 w-full cursor-default">
                ✅ 已完成打卡
              </button>
            {:else}
              <a href="/login" class="btn btn-primary w-full text-center">
                🔑 登录后打卡
              </a>
            {/if}
            
            <div class="pt-3 border-t border-natural-100">
              <p class="text-sm text-natural-600 mb-3">分享到：</p>
              <div class="flex gap-2">
                <button on:click={() => handleShare('weixin')} class="flex-1 btn btn-outline text-sm py-2">
                  💚 微信
                </button>
                <button on:click={() => handleShare('weibo')} class="flex-1 btn btn-outline text-sm py-2">
                  🔴 微博
                </button>
                <button on:click={() => handleShare('link')} class="flex-1 btn btn-outline text-sm py-2">
                  🔗 链接
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Add to Route -->
        {#if $auth.isAuthenticated}
          <div class="card p-6 bg-gradient-to-br from-sky-50 to-primary-50">
            <h2 class="text-xl font-bold text-natural-800 mb-3">🗺️ 规划路线</h2>
            <p class="text-natural-600 text-sm mb-4">将这个角落添加到你的探索路线中</p>
            <button class="btn btn-secondary w-full" on:click={() => goto('/routes')}>
              创建路线
            </button>
          </div>
        {/if}
      </div>
    </div>
  </div>

  <!-- Checkin Modal -->
  {#if showCheckinModal}
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" on:click={() => showCheckinModal = false}></div>
      <div class="relative card p-6 w-full max-w-md animate-slide-up">
        <h3 class="text-xl font-bold text-natural-800 mb-4">✍️ 写下你的打卡感受</h3>
        
        <div class="space-y-4">
          <div>
            <label class="label">评分</label>
            <div class="flex gap-2">
              {#each [1, 2, 3, 4, 5] as star}
                <button
                  on:click={() => checkinRating = star}
                  class="text-3xl transition-transform hover:scale-110"
                  type="button"
                >
                  {star <= checkinRating ? '⭐' : '☆'}
                </button>
              {/each}
            </div>
          </div>
          
          <div>
            <label class="label">打卡留言（选填）</label>
            <textarea
              bind:value={checkinContent}
              class="input min-h-[120px] resize-none"
              placeholder="分享你的探索体验..."
            ></textarea>
          </div>
          
          <div class="flex gap-3 pt-2">
            <button on:click={() => showCheckinModal = false} class="btn btn-outline flex-1" type="button">
              取消
            </button>
            <button on:click={handleCheckin} class="btn btn-primary flex-1" disabled={checkinLoading}>
              {#if checkinLoading}
                <span class="inline-flex items-center gap-2">
                  <span class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                  提交中
                </span>
              {:else}
                确认打卡
              {/if}
            </button>
          </div>
        </div>
      </div>
    </div>
  {/if}
{:else}
  <div class="max-w-2xl mx-auto text-center py-20">
    <div class="text-6xl mb-4">😕</div>
    <h2 class="text-2xl font-bold text-natural-800 mb-2">角落不存在</h2>
    <p class="text-natural-600 mb-6">这个角落可能已经被移除或隐藏了</p>
    <a href="/corners" class="btn btn-primary">返回发现页</a>
  </div>
{/if}
