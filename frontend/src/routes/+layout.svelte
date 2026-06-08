<script>
  import '../app.css';
  import { page } from '$app/stores';
  import { onMount } from 'svelte';
  import { auth } from '$lib/stores/auth';
  import { achievements as achievementStore } from '$lib/stores/achievements';
  import Navbar from '$lib/components/Navbar.svelte';
  import Toast from '$lib/components/Toast.svelte';
  import AchievementUnlockModal from '$lib/components/AchievementUnlockModal.svelte';

  let unlockModalOpen = false;
  let currentUnlockAchievement = null;

  onMount(() => {
    window.addEventListener('achievement:unlock', handleAchievementUnlock);
    
    if ($auth.isAuthenticated) {
      achievementStore.checkForNewAchievements();
    }
  });

  function handleAchievementUnlock(event) {
    currentUnlockAchievement = event.detail;
    unlockModalOpen = true;
  }

  $: isAuthPage = $page.url.pathname === '/login' || $page.url.pathname === '/register';
</script>

<div class="min-h-screen">
  {#if !isAuthPage}
    <Navbar />
  {/if}
  
  <main class="{!isAuthPage ? 'pt-20' : ''}">
    <slot />
  </main>
  
  <Toast />
  
  <AchievementUnlockModal
    bind:isOpen={unlockModalOpen}
    bind:achievement={currentUnlockAchievement}
  />
</div>

<style>
  @import '../app.css';

  @keyframes slide-up {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  .animate-slide-up {
    animation: slide-up 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  }

  .animate-fade-in {
    animation: fadeIn 0.3s ease-out;
  }

  :global(html) {
    scroll-behavior: smooth;
  }

  :global(body) {
    @apply bg-gradient-to-br from-natural-50 via-primary-50/30 to-sky-50/30 min-h-screen;
  }

  :global(.leaflet-container) {
    @apply rounded-xl overflow-hidden;
  }
</style>
