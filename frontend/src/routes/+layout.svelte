<script>
  import '../app.css';
  import Navbar from '$lib/components/Navbar.svelte';
  import Toast from '$lib/components/Toast.svelte';
  import { page } from '$app/stores';

  $: isAuthPage = $page.url.pathname === '/login' || $page.url.pathname === '/register';
</script>

{#if !isAuthPage}
  <Navbar />
{/if}

<main class="{!isAuthPage ? 'pt-20 pb-24 md:pb-8' : ''} min-h-screen">
  <slot />
</main>

<Toast />
