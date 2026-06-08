<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { auth } from '$lib/stores/auth';
  import { getCurrentUser, getUserStats, updateUser } from '$lib/api/auth';
  import { getCheckins } from '$lib/api/checkins';
  import Loading from '$lib/components/Loading.svelte';
  import { toast } from '$lib/stores/toast';

  let user = null;
  let userStats = null;
  let recentCheckins = [];
  let loading = true;
  let editing = false;
  let editAvatar = '';
  let editBio = '';
  let saving = false;
  let avatarFile = null;
  let avatarPreview = '';

  const statItems = [
    { key: 'total_corners', label: '发布角落', icon: '📍', color: 'text-primary-600' },
    { key: 'total_checkins', label: '打卡记录', icon: '✅', color: 'text-sky-600' },
    { key: 'total_routes', label: '路线规划', icon: '🗺️', color: 'text-amber-600' },
    { key: 'total_achievements', label: '获得成就', icon: '🏆', color: 'text-purple-600' },
    { key: 'total_shares', label: '分享次数', icon: '📤', color: 'text-pink-600' },
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
      const [userData, statsData, checkinsData] = await Promise.all([
        getCurrentUser(),
        getUserStats(),
        getCheckins({ limit: 5 })
      ]);

      user = userData;
      userStats = statsData;
      recentCheckins = checkinsData?.items || checkinsData || [];

      editAvatar = user.avatar || '';
      editBio = user.bio || '';
      avatarPreview = user.avatar || '';
    } catch (error) {
      toast.error('加载个人信息失败');
    } finally {
      loading = false;
    }
  }

  function startEdit() {
    editAvatar = user.avatar || '';
    editBio = user.bio || '';
    avatarPreview = user.avatar || '';
    avatarFile = null;
    editing = true;
  }

  function cancelEdit() {
    editing = false;
    avatarFile = null;
  }

  function handleAvatarChange(e) {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        toast.error('图片大小不能超过5MB');
        return;
      }
      avatarFile = file;
      const reader = new FileReader();
      reader.onload = (event) => {
        avatarPreview = event.target?.result;
      };
      reader.readAsDataURL(file);
    }
  }

  async function handleSave() {
    if (!editBio.trim()) {
      toast.error('个人简介不能为空');
      return;
    }

    saving = true;
    try {
      let avatarUrl = editAvatar;
      
      if (avatarFile) {
        const formData = new FormData();
        formData.append('file', avatarFile);
        
        const uploadRes = await fetch('/api/upload', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: formData
        });
        
        if (uploadRes.ok) {
          const uploadData = await uploadRes.json();
          avatarUrl = uploadData.url;
        } else {
          toast.error('头像上传失败');
          return;
        }
      }

      const updatedUser = await updateUser({
        avatar: avatarUrl,
        bio: editBio.trim()
      });

      user = updatedUser;
      auth.fetchCurrentUser();
      
      editing = false;
      avatarFile = null;
      toast.success('个人资料更新成功');
    } catch (error) {
      toast.error(error.response?.data?.detail || '保存失败，请重试');
    } finally {
      saving = false;
    }
  }

  function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  function getCategoryIcon(category) {
    const icons = {
      '人文古迹': '🏛️',
      '自然风光': '🌿',
      '文艺空间': '📚',
      '艺术创意': '🎨',
      '体验工坊': '🛠️',
      '美食探店': '🍜'
    };
    return icons[category] || '📍';
  }

  function handleLogout() {
    auth.logout();
    toast.success('已退出登录');
    goto('/login');
  }
</script>

{#if loading}
  <Loading fullscreen text="正在加载个人中心..." />
{:else if user}
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-natural-800 mb-2">个人中心</h1>
      <p class="text-natural-600">管理你的个人信息，查看探索记录</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-1">
        <div class="card p-6">
          <div class="text-center mb-6">
            <div class="relative inline-block">
              <img
                src={user.avatar || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + user.username}
                alt={user.username}
                class="w-32 h-32 rounded-full mx-auto border-4 border-primary-100 shadow-soft object-cover"
              />
              <div class="absolute bottom-0 right-0 w-10 h-10 bg-primary-500 rounded-full flex items-center justify-center text-white text-xl border-4 border-white">
                ✨
              </div>
            </div>
            <h2 class="text-2xl font-bold text-natural-800 mt-4">{user.username}</h2>
            <p class="text-natural-500 text-sm mt-1">加入于 {formatDate(user.created_at)}</p>
            {#if user.bio}
              <p class="text-natural-600 mt-3 text-sm leading-relaxed">{user.bio}</p>
            {:else}
              <p class="text-natural-400 mt-3 text-sm italic">这个人很懒，还没有填写简介~</p>
            {/if}
          </div>

          <div class="space-y-3">
            <button
              on:click={startEdit}
              class="w-full btn btn-primary flex items-center justify-center gap-2"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
              </svg>
              编辑资料
            </button>
            <button
              on:click={handleLogout}
              class="w-full btn btn-outline text-red-500 border-red-200 hover:border-red-400 hover:text-red-600 hover:bg-red-50 flex items-center justify-center gap-2"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
              </svg>
              退出登录
            </button>
          </div>
        </div>
      </div>

      <div class="lg:col-span-2 space-y-6">
        <div class="card p-6">
          <h3 class="text-xl font-bold text-natural-800 mb-4 flex items-center gap-2">
            <span>📊</span>
            我的数据
          </h3>
          <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
            {#each statItems as stat}
              <div class="text-center p-4 bg-gradient-to-br from-natural-50 to-white rounded-xl border border-natural-100">
                <div class="text-3xl mb-2">{stat.icon}</div>
                <div class="text-2xl font-bold {stat.color}">{userStats?.[stat.key] || 0}</div>
                <div class="text-xs text-natural-500 mt-1">{stat.label}</div>
              </div>
            {/each}
          </div>
        </div>

        <div class="card p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-xl font-bold text-natural-800 flex items-center gap-2">
              <span>📝</span>
              最近打卡
            </h3>
            <a href="/corners" class="text-primary-600 hover:text-primary-700 text-sm font-medium flex items-center gap-1">
              查看全部
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
              </svg>
            </a>
          </div>

          {#if recentCheckins.length > 0}
            <div class="space-y-3">
              {#each recentCheckins as checkin}
                <div
                  class="flex items-center gap-4 p-4 bg-gradient-to-r from-natural-50 to-white rounded-xl border border-natural-100 hover:border-primary-200 hover:shadow-soft transition-all cursor-pointer"
                  on:click={() => goto(`/corners/${checkin.corner?.id}`)}
                >
                  <div class="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center text-2xl flex-shrink-0">
                    {getCategoryIcon(checkin.corner?.category)}
                  </div>
                  <div class="flex-1 min-w-0">
                    <h4 class="font-semibold text-natural-800 truncate">{checkin.corner?.title}</h4>
                    <p class="text-sm text-natural-500 truncate">{checkin.corner?.category}</p>
                  </div>
                  <div class="text-right flex-shrink-0">
                    <p class="text-xs text-natural-400">{formatDate(checkin.created_at)}</p>
                    {#if checkin.rating}
                      <div class="flex items-center gap-0.5 mt-1 justify-end">
                        {#each Array(checkin.rating) as _, i}
                          <span class="text-amber-400 text-xs">⭐</span>
                        {/each}
                      </div>
                    {/if}
                  </div>
                  <svg class="w-5 h-5 text-natural-300 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                  </svg>
                </div>
              {/each}
            </div>
          {:else}
            <div class="text-center py-12">
              <div class="text-5xl mb-4">🌱</div>
              <p class="text-natural-600 mb-4">还没有打卡记录</p>
              <a href="/corners" class="btn btn-primary">去探索角落</a>
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>

  {#if editing}
    <div class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl shadow-card w-full max-w-md animate-slide-up max-h-[90vh] overflow-y-auto">
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-xl font-bold text-natural-800">编辑个人资料</h3>
            <button
              on:click={cancelEdit}
              class="text-natural-400 hover:text-natural-600 transition-colors"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <div class="space-y-6">
            <div class="text-center">
              <div class="relative inline-block">
                <img
                  src={avatarPreview || 'https://api.dicebear.com/7.x/avataaars/svg?seed=' + user.username}
                  alt="头像预览"
                  class="w-24 h-24 rounded-full mx-auto border-4 border-primary-100 object-cover"
                />
                <label class="absolute bottom-0 right-0 w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center text-white cursor-pointer hover:bg-primary-600 transition-colors">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/>
                  </svg>
                  <input
                    type="file"
                    accept="image/*"
                    on:change={handleAvatarChange}
                    class="hidden"
                  />
                </label>
              </div>
              <p class="text-xs text-natural-500 mt-2">点击相机图标更换头像</p>
            </div>

            <div>
              <label class="label">用户名</label>
              <input
                type="text"
                value={user.username}
                disabled
                class="input bg-natural-50 text-natural-500 cursor-not-allowed"
              />
              <p class="text-xs text-natural-400 mt-1">用户名不可修改</p>
            </div>

            <div>
              <label class="label">个人简介</label>
              <textarea
                bind:value={editBio}
                class="input min-h-[120px] resize-none"
                placeholder="介绍一下自己吧，让大家认识你~"
                maxlength={200}
              />
              <p class="text-xs text-natural-400 mt-1 text-right">{editBio.length}/200</p>
            </div>

            <div class="flex gap-3 pt-2">
              <button
                on:click={cancelEdit}
                class="flex-1 btn btn-outline"
                disabled={saving}
              >
                取消
              </button>
              <button
                on:click={handleSave}
                class="flex-1 btn btn-primary"
                disabled={saving}
              >
                {#if saving}
                  <span class="inline-flex items-center gap-2">
                    <span class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                    保存中...
                  </span>
                {:else}
                  保存
                {/if}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  {/if}
{/if}
