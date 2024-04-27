<script>
  import { onMount } from 'svelte';
  import { WEBUI_API_BASE_URL } from '$lib/constants';

  const clientId = '763749380527-s493gmjqulracsgaa4ae4umr2pj8k7kv.apps.googleusercontent.com';
  const loginURI = `http://localhost:8080/api/v1/auths/auth/google`;

  async function handleCredentialResponse(response) {
    console.log('Encoded JWT ID token from Google:', response.credential);
    try {
      const res = await fetch(loginURI, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token: response.credential }),
      });

      if (!res.ok) {
        throw new Error(`Backend authentication failed: ${res.statusText}`);
      }

      const data = await res.json();
      conosle.log(data)
      localStorage.setItem('joken', data.joken);
      window.location.href = 'http://localhost:5173'; // Adjust if your home page URL is different   
	 } catch (error) {
      console.error('Error:', error);
    }
  }

  onMount(() => {
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.onload = () => {
      google.accounts.id.initialize({
        client_id: clientId,
        callback: handleCredentialResponse,
        ux_mode: 'popup',
        login_uri: loginURI,
      });
      google.accounts.id.renderButton(
        document.getElementById('buttonDiv'),
        { theme: 'outline', size: 'large' }
      );
      google.accounts.id.prompt();
    };
    document.body.appendChild(script);

    return () => document.body.removeChild(script);
  });
</script>

<div id="buttonDiv"></div>
