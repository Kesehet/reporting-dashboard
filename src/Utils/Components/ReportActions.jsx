import React, { useState } from 'react';
import { Button } from 'primereact/button';
import { Dialog } from 'primereact/dialog';
import { DataTable } from 'primereact/datatable';
import { exportReportAsCSV, resolveReportRows } from './Utils';

export default function ReportActions({ report, filename = 'exported_data.csv', dialogHeader = 'Detailed Data' }) {
    const [dialogVisible, setDialogVisible] = useState(false);
    const [dialogData, setDialogData] = useState(null);

    const showDialog = async () => {
        setDialogData(await resolveReportRows(report));
        setDialogVisible(true);
    };

    const exportReport = async () => {
        await exportReportAsCSV(report, filename);
    };

    return (
        <>
            <Button
                icon="pi pi-file"
                label="Export"
                onClick={exportReport}
                className="p-button-text"
            />
            <Button
                icon="pi pi-eye"
                label="View"
                onClick={showDialog}
                className="p-button-text"
            />
            <Dialog
                header={dialogHeader}
                visible={dialogVisible}
                style={{ width: '100vw', height: '100vh', margin: '0 auto' }}
                onHide={() => setDialogVisible(false)}
                footer={(
                    <Button
                        label="Close"
                        icon="pi pi-times"
                        onClick={() => setDialogVisible(false)}
                    />
                )}
                maximizable
            >
                {dialogData && dialogData.length > 0 ? (
                    <DataTable value={dialogData} paginator rows={10} className="p-datatable-responsive p-datatable-sm">
                        <DataTable.Column field="Date" header="Date" sortable />
                        {Object.keys(dialogData[0]).map((key) => key === 'Date' ? null : (
                            <DataTable.Column key={key} field={key} header={key} sortable />
                        ))}
                    </DataTable>
                ) : (
                    <div style={{ textAlign: 'center', padding: '2rem' }}>
                        <p>No data to display</p>
                    </div>
                )}
            </Dialog>
        </>
    );
}
