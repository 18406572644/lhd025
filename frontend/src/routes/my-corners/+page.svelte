<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { auth } from '$lib/stores/auth';
  import { cornerStore } from '$lib/stores/corners';
  import CornerCard from '$lib/components/CornerCard.svelte';
  import Loading from '$lib/components/Loading.svelte';
  import { toast } from '$lib/stores/toast';

  let corners = [];
  let loading = true;
  let showDeleteModal = false;
  let deleteCornerId = null;

  onMount(async () => {
    if (!$auth.isAuthenticated) {
      toast.warning('请先登录');
      goto('/login');
      return;
    }
    await loadCorners();
  });

  async function loadCorners() {
    loading = true;
    try {
      const allCorners = await cornerStore.fetchCorners();
      if (allCorners) {
        corners = allCorners.filter(c => c.author_id === $auth.user?.id);
      }
    } catch (error) {
      toast.error('加载失败');
    } finally {
      loading = false;
    }
  }

  function confirmDelete(cornerId) {
    deleteCornerId = cornerId;
    showDeleteModal = true;
  }

  async function handleDelete() {
    if (!deleteCornerId) return;
    
    try {
      const result = await cornerStore.deleteCorner(deleteCornerId);
      if (result.success) {
        toast.success('删除成功');
        corners = corners.filter(c => c.id !== deleteCornerId);
      } else {
        toast.error(result.error);
      }
    } catch (error) {
      toast.error('删除失败');
    } finally {
      showDeleteModal = false;
      deleteCornerId = null;
    }
  }
</script>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
  <div class="flex items-center justify-between mb-8">
    <div>
      <h1 class="text-3xl font-bold text-natural-800 mb-2">我的角落</h1>
      <p class="text-natural-600">管理你发布的所有城市角落</p>
    </div>
    <a href="/publish" class="btn btn-primary">
      + 发布新角落
    </a>
  </div>

  {#if loading}
    <Loading text="加载中..." />
  {:else if corners.length > 0}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {#each corners as corner}
        <div class="relative group">
          <CornerCard {corner} />
          <button
            on:click={() => confirmDelete(corner.id)}
            class="absolute top-3 right-3 z-10 w-8 h-8 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center hover:bg-red-600"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
          </button>
        </div>
      {/each}
    </div>
  {:else}
    <div class="card p-12 text-center">
      <div class="text-5xl mb-4">📍</div>
      <h3 class="text-xl font-bold text-natural-800 mb-2">还没有发布任何角落</h3>
      <p class="text-natural-600 mb-6">分享你发现的城市秘密，让更多人探索这些美好</p>
      <a href="/publish" class="btn btn-primary">发布第一个角落</a>
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
        <p class="text-natural-600 mb-6">删除后将无法恢复，确定要删除这个角落吗？</p>
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
