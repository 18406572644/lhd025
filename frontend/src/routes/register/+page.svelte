<script>
  import { goto } from '$app/navigation';
  import { auth } from '$lib/stores/auth';
  import { toast } from '$lib/stores/toast';

  let username = '';
  let email = '';
  let password = '';
  let confirmPassword = '';
  let loading = false;

  async function handleRegister(e) {
    e.preventDefault();
    
    if (!username || !email || !password || !confirmPassword) {
      toast.error('请填写完整信息');
      return;
    }

    if (password !== confirmPassword) {
      toast.error('两次输入的密码不一致');
      return;
    }

    if (password.length < 6) {
      toast.error('密码长度至少6位');
      return;
    }

    loading = true;
    const result = await auth.register({ username, email, password });
    loading = false;

    if (result.success) {
      toast.success('注册成功！请登录');
      goto('/login');
    } else {
      toast.error(result.error);
    }
  }
</script>

<div class="min-h-screen flex items-center justify-center px-4 bg-gradient-to-br from-sky-50 via-white to-primary-50">
  <div class="w-full max-w-md">
    <div class="text-center mb-8 animate-fade-in">
      <div class="text-6xl mb-4">🌿</div>
      <h1 class="text-3xl font-bold gradient-text mb-2">角落探索</h1>
      <p class="text-natural-600">开启你的城市探索之旅</p>
    </div>

    <div class="card p-8 animate-slide-up">
      <h2 class="text-2xl font-bold text-natural-800 mb-6 text-center">创建账号</h2>

      <form on:submit={handleRegister} class="space-y-4">
        <div>
          <label class="label">用户名</label>
          <input
            type="text"
            bind:value={username}
            class="input"
            placeholder="请输入用户名（3-50字符）"
            disabled={loading}
          />
        </div>

        <div>
          <label class="label">邮箱</label>
          <input
            type="email"
            bind:value={email}
            class="input"
            placeholder="请输入邮箱地址"
            disabled={loading}
          />
        </div>

        <div>
          <label class="label">密码</label>
          <input
            type="password"
            bind:value={password}
            class="input"
            placeholder="请输入密码（至少6位）"
            disabled={loading}
          />
        </div>

        <div>
          <label class="label">确认密码</label>
          <input
            type="password"
            bind:value={confirmPassword}
            class="input"
            placeholder="请再次输入密码"
            disabled={loading}
          />
        </div>

        <button
          type="submit"
          class="btn btn-primary w-full py-3 text-base mt-6"
          disabled={loading}
        >
          {#if loading}
            <span class="inline-flex items-center gap-2">
              <span class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              注册中...
            </span>
          {:else}
            注册
          {/if}
        </button>
      </form>

      <div class="mt-6 text-center">
        <p class="text-natural-600">
          已有账号？
          <a href="/login" class="text-primary-600 font-medium hover:underline">
            立即登录
          </a>
        </p>
      </div>
    </div>
  </div>
</div>
