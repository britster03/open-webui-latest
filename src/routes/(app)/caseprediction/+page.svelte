<script>
    import { casePrediction } from '$lib/apis/caseprediction';
    import { PDFDocument } from 'pdfjs';
    import { user } from '$lib/stores';
    import Navbar from '$lib/components/layout/Navbar.svelte';
    import MessageInput from '$lib/components/chat/MessageInput.svelte';
    import Message from '$lib/components/chat/Message.svelte';

    let legalQuery = '';
    let file = null;
    let messages = [];
    let loading = false;
    let loadingPercentage = 0;
    let isSubmitting = false;
    let abortController = null;

    function updateProgress(endAt, increment = 5, interval = 100) {
        const intervalId = setInterval(() => {
            if (loadingPercentage >= endAt) {
                clearInterval(intervalId);
                if (endAt === 100) {
                    loading = false;  // stops loading when progress reaches 100%
                }
            } else {
                loadingPercentage += increment;
            }
        }, interval);
    }

    async function extractTextFromPDF(pdfBuffer) {
        loading = true;
        loadingPercentage = 0;
        updateProgress(30); // count progress during PDF loading

        const pdfDoc = await PDFDocument.load(pdfBuffer);
        const pages = pdfDoc.getPages();
        const textPromises = pages.map((page, index) => {
            return page.getTextContent().then(textContent => {
                loadingPercentage = 30 + ((index + 1) / pages.length * 40); // update the progress from 30 to 70
                return textContent.items.map(item => item.str).join(' ');
            });
        });
        const textContents = await Promise.all(textPromises);
        loadingPercentage = 70; // reaching completion of text extraction
        return textContents.join('\n');
    }

    async function performCasePrediction() {
        if (!legalQuery.trim() && !file) {
            console.error("Please enter a query or upload a PDF file for prediction");
            return;
        }

        isSubmitting = true;
        loading = true;
        loadingPercentage = 0;
        updateProgress(10); // initial progress for starting the process

        let queryText = legalQuery;
        if (file) {
            const buffer = await file.arrayBuffer();
            queryText = await extractTextFromPDF(buffer);
        }

        // Assume backend processing starts from 50%
        updateProgress(80,2,150); // update progress to mid-way for starting backend processing
        try {
            const token = user.token;
            abortController = new AbortController();
            const response = await casePrediction(token, queryText, abortController.signal);
            if (!abortController.signal.aborted) {
                updateProgress(80,2,150); // completing the loading once response is received
                messages = [
                    ...messages,
//                    { id: Date.now(), content: queryText, role: 'user' },
//                    { id: Date.now() + 1, content: response.reasoning, role: 'assistant', label: response.prediction ? 'Accepted' : 'Rejected' }
                    { id: Date.now(), content: `<strong>Query:</strong> ${queryText}`, role: 'user' },
                    { id: Date.now() + 1, content: `<strong>Prediction:</strong> ${response.prediction ? 'Accepted' : 'Rejected'}<br><strong>Reasoning:</strong> ${response.reasoning}`, role: 'assistant' }
                ];
            }
            legalQuery = '';
            file = null;
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log("Prediction request was canceled.");
            } else {
                console.error("Failed to perform case prediction:", error);
            }
        } finally {
            isSubmitting = false;
            abortController = null;
        }
    }

    function cancelPrediction() {
        if (abortController) {
            abortController.abort();
            messages = [...messages, { id: Date.now(), content: "Prediction request canceled by the user.", role: 'system' }];
            loading = false;
            isSubmitting = false;
            loadingPercentage = 0; // reset progress when canceled
        }
    }
</script>

<style>
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

</style>


<svelte:head>
    <title>Legal Case Prediction</title>
</svelte:head>

<div class="h-screen max-h-[100dvh] w-full flex flex-col">
    <Navbar />
    <MessageInput bind:prompt={legalQuery} on:fileSelected="{e => file = e.detail.file}" submitPrompt={performCasePrediction} disabled={isSubmitting} />
    {#if isSubmitting}
        <div class="loading-indicator">
            Loading... {Math.round(loadingPercentage)}%
        </div>
        <button on:click={cancelPrediction} disabled={!loading} class="cancel-button">Cancel</button>
    {/if}
    
    <div class="messages-container">
        {#each messages as message}
            <div class={`message ${message.role}`}>
                {@html message.content}
            </div>
        {/each}
    </div>

</div>
