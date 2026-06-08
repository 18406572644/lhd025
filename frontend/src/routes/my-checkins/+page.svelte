<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { auth } from '$lib/stores/auth';
  import { getCheckins, deleteCheckin } from '$lib/api/checkins';
  import Loading from '$lib/components/Loading.svelte';
  import { toast } from '$lib/stores/toast';

  let checkins = [];
  let loading = true;
  let showDeleteModal = false;
  let deleteCheckinId = null;

  const categoryIcons = {
    '人文古迹': '🏛️',
    '自然风光': '🌿',
    '文艺空间': '📚',
    '艺术创意': '🎨',
    '体验工坊': '🛠️',
    '美食探店': '🍜',
    '其他': '📍'
  };

  onMount(async () => {
    if (!$auth.isAuthenticated) {
      toast.warning('请先登录');
      goto('/login');
      return;
    }
    await loadCheckins();
  });

  async function loadCheckins() {
    loading = true;
    try {
      const data = await getCheckins({ user_id: $auth.user?.id });
      if (data) {
        checkins = data;
      }
    } catch (error) {
      toast.error('加载失败');
    } finally {
      loading = false;
    }
  }

  function confirmDelete(checkinId) {
    deleteCheckinId = checkinId;
    showDeleteModal = true;
  }

  async function handleDelete() {
    if (!deleteCheckinId) return;
    
    try {
      await deleteCheckin(deleteCheckinId);
      toast.success('删除成功');
      checkins = checkins.filter(c => c.id !== deleteCheckinId);
    } catch (error) {
      toast.error('删除失败');
    } finally {
      showDeleteModal = false;
      deleteCheckinId = null;
    }
  }

  function getStars(rating) {
    return '⭐'.repeat(rating) + '☆'.repeat(5 - rating);
  }

  function goToCorner(cornerId) {
    goto(`/corners/${cornerId}`);
  }
</script>

<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-natural-800 mb-2">我的打卡</h1>
    <p class="text-natural-600">记录你探索过的每一个角落</p>
  </div>

  {#if loading}
    <Loading text="加载中..." />
  {:else if checkins.length > 0}
    <div class="space-y-4">
      {#each checkins as checkin}
        <div class="card p-5 hover:shadow-hover transition-shadow">
          <div class="flex gap-4">
            <div
              class="w-24 h-24 rounded-xl overflow-hidden flex-shrink-0 cursor-pointer"
              on:click={() => goToCorner(checkin.corner_id)}
            >
              <img
                src={checkin.corner?.images || 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400'}
                alt={checkin.corner?.title}
                class="w-full h-full object-cover hover:scale-110 transition-transform duration-300"
              />
            </div>
            
            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between gap-4">
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-1">
                    <span class="text-xl">{categoryIcons[checkin.corner?.category] || '📍'}</span>
                    <h3
                      class="font-bold text-natural-800 hover:text-primary-600 cursor-pointer truncate"
                      on:click={() => goToCorner(checkin.corner_id)}
                    >
                      {checkin.corner?.title}
                    </h3>
                  </div>
                  <div class="flex items-center gap-3 text-sm text-natural-500 mb-2">
                    <span class="badge badge-primary text-xs">{checkin.corner?.category}</span>
                    <span>{new Date(checkin.created_at).toLocaleDateString()}</span>
                  </div>
                  <div class="text-yellow-500 text-sm mb-2">{getStars(checkin.rating)}</div>
                  {#if checkin.content}
                    <p class="text-natural-600 text-sm line-clamp-2">{checkin.content}</p>
                  {/if}
                </div>
                <button
                  on:click={() => confirmDelete(checkin.id)}
                  class="p-2 text-natural-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors flex-shrink-0"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {:else}
    <div class="card p-12 text-center">
      <div class="text-5xl mb-4">✅</div>
      <h3 class="text-xl font-bold text-natural-800 mb-2">还没有打卡记录</h3>
      <p class="text-natural-600 mb-6">去探索城市的角落，记录你的发现吧！</p>
      <a href="/corners" class="btn btn-primary">开始探索</a>
    </div>
  {/if}
</div>

{#if showDeleteModal}
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" on:click={() => showDeleteModal = false}></div>
    <div class="relative card p-6 w-full max-w-sm animate-slide-up">
      <div class="text-center">
        <div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
          </svg>
        </div>
        <h3 class="text-xl font-bold text-natural-800 mb-2">确认删除</h3>
        <p class="text-natural-600 mb-6">删除后将无法恢复，确定要删除这条打卡记录吗？</p>
        <div class="flex gap-3">
          <button on:click={() => showDeleteModal = false} class="btn btn-outline flex-1">
            取消
          </button>
          <button on:click={handleDelete} class="btn btn-danger flex-1">
            确认删除
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}
