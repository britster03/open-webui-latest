import { CASE_API_BASE_URL } from '$lib/constants';

export const casePrediction = async (token: string, query: string) => {
    const response = await fetch(`${CASE_API_BASE_URL}/caseprediction`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ query })
    }).then(res => {
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
    }).catch(err => {
        console.error("Fetch error:", err);
        throw err;
    });

    return response;
};


