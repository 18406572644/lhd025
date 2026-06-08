<script>
  import { goto } from '$app/navigation';
  import { auth } from '$lib/stores/auth';
  import { toast } from '$lib/stores/toast';

  let username = '';
  let password = '';
  let loading = false;

  async function handleLogin(e) {
    e.preventDefault();
    if (!username || !password) {
      toast.error('请填写用户名和密码');
      return;
    }

    loading = true;
    const result = await auth.login({ username, password });
    loading = false;

    if (result.success) {
      toast.success('登录成功！欢迎回来');
      goto('/');
    } else {
      toast.error(result.error);
    }
  }
</script>

<div class="min-h-screen flex items-center justify-center px-4 bg-gradient-to-br from-primary-50 via-white to-sky-50">
  <div class="w-full max-w-md">
    <div class="text-center mb-8 animate-fade-in">
      <div class="text-6xl mb-4">🌿</div>
      <h1 class="text-3xl font-bold gradient-text mb-2">角落探索</h1>
      <p class="text-natural-600">发现城市里的每一处美好</p>
    </div>

    <div class="card p-8 animate-slide-up">
      <h2 class="text-2xl font-bold text-natural-800 mb-6 text-center">登录账号</h2>

      <form on:submit={handleLogin} class="space-y-5">
        <div>
          <label class="label">用户名</label>
          <input
            type="text"
            bind:value={username}
            class="input"
            placeholder="请输入用户名"
            disabled={loading}
          />
        </div>

        <div>
          <label class="label">密码</label>
          <input
            type="password"
            bind:value={password}
            class="input"
            placeholder="请输入密码"
            disabled={loading}
          />
        </div>

        <button
          type="submit"
          class="btn btn-primary w-full py-3 text-base"
          disabled={loading}
        >
          {#if loading}
            <span class="inline-flex items-center gap-2">
              <span class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              登录中...
            </span>
          {:else}
            登录
          {/if}
        </button>
      </form>

      <div class="mt-6 text-center">
        <p class="text-natural-600">
          还没有账号？
          <a href="/register" class="text-primary-600 font-medium hover:underline">
            立即注册
          </a>
        </p>
      </div>

      <div class="mt-6 p-4 bg-primary-50 rounded-xl">
        <p class="text-sm text-primary-700 text-center">
          💡 测试账号：explorer1 / 123456
        </p>
      </div>
    </div>
  </div>
</div>
