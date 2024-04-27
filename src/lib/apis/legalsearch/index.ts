// src/lib/apis/legalsearch/index.ts
import { LEGAL_API_BASE_URL } from '$lib/constants';

export const legalSearch = async (token:string, query: string) => {
    let error = null;

    const response = await fetch(`${LEGAL_API_BASE_URL}/legalsearch`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
	    Authorization : `Bearer ${token}`
        },
        body: JSON.stringify({ query })
    }).then(res => {
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
    }).catch(err => {
        console.error("Fetch error:", err);
        error = err;
    });

    if (error) {
        throw new Error("Error performing legal search");
    }

    return response;
};

