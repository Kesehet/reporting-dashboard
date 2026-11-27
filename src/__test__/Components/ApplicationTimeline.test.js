import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import ApplicationTimeline from '../../Utils/Components/ApplicationTimeline';

test('shows related transactions in date order with inline comments and no workflow steps', async () => {
    const spy = jest.spyOn(global, 'fetch').mockResolvedValue({
        ok: true, json: async () => ({
            job_reference: 'C-ROOT', status: 'Completed',
            transactions: [
                {tracking_code: 'C-ROOT', name: 'Consumer Loans', created: '2026-11-22T18:00:00Z', comments: []},
                {tracking_code: 'C-TASK', name: 'Consumer Review', group: 'Manual Review',
                 created: '2026-11-23T18:00:00Z', comments: [{message: 'Review note'}]},
            ],
            application_comments: [{message: 'Application note', time: '2026-11-22T19:00:00Z'}],
        })
    });
    try {
        const { container } = render(<ApplicationTimeline trackingCode="C-ROOT" />);
        await waitFor(() => expect(screen.getByText('Review note')).toBeInTheDocument());
        const cards = container.querySelectorAll('.application-timeline__history > .application-timeline__task');
        expect(cards).toHaveLength(3);
        expect(within(cards[0]).getByText('C-TASK')).toBeInTheDocument();
        expect(within(cards[0]).getByText('Review note')).toBeInTheDocument();
        expect(within(cards[1]).getByText('Application note')).toBeInTheDocument();
        expect(within(cards[2]).getByText('C-ROOT')).toBeInTheDocument();
        expect(screen.queryByText(/^STEP /)).not.toBeInTheDocument();
        expect(screen.queryByText(/Transactions not linked/)).not.toBeInTheDocument();
        expect(spy.mock.calls[0][0]).toContain('tracking_code=C-ROOT');
    } finally { spy.mockRestore(); }
});

test('old backend responses also show one transaction history without step cards', async () => {
    const spy = jest.spyOn(global, 'fetch').mockResolvedValue({
        ok: true, json: async () => ({
            steps: [{name: 'Start', tasks: [{tracking_code: 'C-ROOT', comments: []}], comments: []}],
            unassigned_tasks: [{tracking_code: 'C-TASK', comments: [{message: 'Older backend note'}]}],
            unassigned_comments: [],
        })
    });
    try {
        render(<ApplicationTimeline trackingCode="C-ROOT" />);
        await waitFor(() => expect(screen.getByText('Older backend note')).toBeInTheDocument());
        expect(screen.getByText('C-ROOT')).toBeInTheDocument();
        expect(screen.getByText('C-TASK')).toBeInTheDocument();
        expect(screen.queryByText('Start')).not.toBeInTheDocument();
    } finally { spy.mockRestore(); }
});
