<script lang="ts">
    export let messages = [];
</script>

<style>
  .messages-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 16px;
    overflow-y: auto;
    align-items: center; /* Align items in the center */
    width: 100%;
  }

  .message {
    padding: 8px 16px;
    border-radius: 0.5rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    max-width: 75%; /* Adjust if necessary to fit your design */
    word-break: break-word;
    background-color: #f3f4f6; /* Light background for all messages */
    color: #1f2937; /* Dark text color for better readability */
  }

  .user {
    margin-left: auto;
    background-color: black; /* Tailwind's 'bg-blue-600' */
    color: white; /* Tailwind's 'text-white' */
  }

  .assistant {
    margin-right: auto;
    background-color: #f3f4f6; /* Tailwind's 'bg-gray-100' */
    color: #1f2937; /* Tailwind's 'text-gray-800' */
  }
</style>



<div class="messages-container flex flex-col p-4 space-y-2">
    {#each messages as message}
        <div class:assistant={message.role === 'assistant'} class:user={message.role === 'user'} class="message">
	   {#if message.label}
             <div class="message-label">{message.label}</div>
      	   {/if}
            <p>{message.content}</p>
        </div>
    {/each}
</div>
