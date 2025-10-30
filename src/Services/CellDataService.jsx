import React, { useEffect, useState } from 'react';
import { normalizeNumber } from '../Utils/Components/Utils';

const CellDataService = ({ query, extraParams = {}, children }) => {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
    const fetchData = async () => {
        let base = process.env.NODE_ENV === 'production'
            ? (window.location.href + "api")
            : "http://localhost:5000";

        const url = `${base}/query`;

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': localStorage.getItem('token'),
                },
                body: JSON.stringify({ query })
            });

            const result = await response.text();
            setData(result);
        } catch (err) {
            console.error(err);
            setError("Unknown Error Occurred.");
        }
    };

        fetchData();
    }, [query]);

    // You can customize how the data is rendered or passed to children
    if (error) return error;
    if (!data) return "Loading...";

    return (
        normalizeNumber(data)
    );
};

export default CellDataService;
