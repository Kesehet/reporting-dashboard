import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import ApplicationTimeline from '../../Utils/Components/ApplicationTimeline';

test('shows workflow steps newest first and preserves task comments', async () => {
    const spy = jest.spyOn(global, 'fetch').mockResolvedValue({
        ok: true, json: async () => ({
            job_reference: 'C-ROOT', status: 'Completed',
            steps: [
                {sequence: 1, name: 'Start', status: 'Completed', tasks: [], comments: []},
                {sequence: 2, name: 'Review Application', status: 'Completed', result: 'Deny',
                    tasks: [{tracking_code: 'C-TASK', name: 'Review', comments: [{message: 'Review note'}]}], comments: []},
            ], unassigned_tasks: [], unassigned_comments: [],
        })
    });
    try {
        render(<ApplicationTimeline trackingCode="C-ROOT" />);
        await waitFor(() => expect(screen.getByText('Review note')).toBeInTheDocument());
        const labels = screen.getAllByText(/^STEP /).map(el => el.textContent);
        expect(labels).toEqual(['STEP 2', 'STEP 1']);
        expect(screen.getByText('C-TASK')).toBeInTheDocument();
        expect(spy.mock.calls[0][0]).toContain('tracking_code=C-ROOT');
    } finally { spy.mockRestore(); }
});
