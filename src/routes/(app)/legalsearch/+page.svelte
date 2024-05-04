<script lang="ts">
    import { onMount, tick } from 'svelte';
    import { legalSearch } from '$lib/apis/legalsearch';
    import { user, WEBUI_NAME } from '$lib/stores';
    import Navbar from '$lib/components/layout/Navbar.svelte';
    import MessageInput from '$lib/components/chat/MessageInput.svelte';
    import Message from '$lib/components/chat/Message.svelte';

    let legalQuery = '';
    let messages = [];
    let loading = false;
    let loadingPercentage = 0;
    let isSubmitting = false;
    let abortController = null;
    let resultsLimit = 8; //default value


    function updateProgress(startAt, endAt, increment = 5, interval = 100) {
        loadingPercentage = startAt;
        const intervalId = setInterval(() => {
            if (loadingPercentage >= endAt) {
                clearInterval(intervalId);
                if (endAt === 100 && !abortController.signal.aborted) {
                    loading = false;
                }
            } else {
                loadingPercentage += increment;
            }
        }, interval);
    }

    const performLegalSearch = async () => {
        if (!legalQuery.trim()) {
            console.error("Please enter a query for legal search");
            return;
        }
        abortController = new AbortController();
        loading = true;
        isSubmitting = true;
        updateProgress(0,80);

        try {
            const token = user.token;
            const response = await legalSearch(token, legalQuery, resultsLimit ,abortController.signal);

            if (abortController.signal.aborted) {
                throw new Error("AbortError");
            }

            updateProgress(50, 100, 10, 50);

            const newMessages = [
                { id: Date.now(), content: legalQuery, role: 'user'},
                ];

//            response.documents.forEach(doc => {
//               newMessages.push({
//                    id: Date.now() + Math.random(), 
//                    content: `Date of Judgement: ${doc.date_of_judgement}, Case Title: ${doc.case_title}, Description: ${doc.short_description}`,
//                    role: 'assistant'
//                });
//          });


            // Modify here to include HTML for line breaks
            response.documents.forEach(doc => {
               newMessages.push({
                    id: Date.now() + Math.random(), // ensuring unique keys
                    content: `<strong>Date of Judgement:</strong> ${doc.date_of_judgement}<br>
                              <strong>Case Title:</strong> ${doc.case_title}<br>
                              <strong>Description:</strong> ${doc.short_description}`,
                    role: 'assistant'
                });
            });

            messages = [...messages, ...newMessages];
            legalQuery = '';
        } catch (error) {
            if (error.name === 'AbortError' || error.message === 'AbortError') {
                console.log("Legal search request was canceled.");
            } else {
                console.error("Failed to perform legal search:", error);
            }
        } finally {
            loading = false;
            loadingPercentage = 0;
            isSubmitting = false;
            abortController = null;
        }
    };

    function cancelLegalSearch() {
        if (abortController) {
            abortController.abort();
            messages = [...messages, { id: Date.now(), content: "Legal search request canceled by the user.", role: 'system' }];
            loading = false;
            loadingPercentage = 0;
            isSubmitting = false;
        }
    }
</script>

<svelte:head>
    <title>Legal Search</title>
</svelte:head>

<div class="h-screen max-h-[100dvh] w-full flex flex-col">
    <Navbar />
    <MessageInput bind:prompt={legalQuery} submitPrompt={performLegalSearch} />
   <div class="input-box"> 
   <label class="results-label">
        No.of Results to be shown (Max. 10):
        <input type="number" bind:value={resultsLimit} min="1" max="10" class="results_input">
    </label>
    </div>
    {#if isSubmitting}
        <button on:click={cancelLegalSearch} class="cancel-button">Cancel Search</button>
    {/if}
    <div class="messages-container">
        {#each messages as message}
            <div class={`message ${message.role}`}>
                {@html message.content}
            </div>
        {/each}
    </div>
    {#if loading}
        <div class="loading-indicator">
            Loading... {Math.round(loadingPercentage)}%
        </div>
    {/if}
</div>

<style>
    .messages-container {
    overflow-y: auto;
    padding: 20px;
    flex-grow: 1;
}
.message {
    margin-bottom: 12px;
    padding: 10px;
    border-radius: 8px;
    width: fit-content;
    max-width: 80%; 
}
.user {
    background-color: #000; 
    color: #fff; 
    align-self: flex-end; 
}
.assistant {
    background-color: #e0e0e0;
    color: #000;
    align-self: flex-start; 
}
.system {
    background-color: #6c757d; 
    color: #fff;
    align-self: flex-start; 
}


    .loading-indicator {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 18px;
        color: white;
        background-color: rgba(0, 0, 0, 0.7);
        padding: 10px 20px;
        border-radius: 10px;
    }
    .cancel-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 10px 20px;
        font-size: 16px;
        color: white;
        background-color: blue;
        border: none;
        border-radius: 5px;
    }

    .input-box {
        margin-left: 20px; 
        padding: 20px; 
        border: 1px solid #ccc; 
        border-radius: 8px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        background-color: #fff; 
        max-width: 550px; 
  }

    .results-label {
        font-size: 16px;
        color: #333;
        display: block;
        margin-bottom: 10px; 
        font-weight: bold;
    }

    .results-input {
        width: 100%; 
        padding: 8px;
        margin-top: 5px; 
        border: 1px solid #ccc;
        border-radius: 4px;
        box-sizing: border-box;
    }

    .results-input:focus {
        border-color: #0056b3;
        box-shadow: 0 0 8px rgba(0, 86, 179, 0.2);
        outline: none;
    }
</style>
