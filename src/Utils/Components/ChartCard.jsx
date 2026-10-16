import React, { useState, useRef } from 'react';
import { Card } from 'primereact/card';
import { Dialog } from 'primereact/dialog';
import { Button } from 'primereact/button';
import html2canvas from 'html2canvas';
import { useEffect } from 'react';
import { clone } from 'chart.js/helpers';

import { toPng } from 'html-to-image';

const ChartCard = ({ title, items, styleNow={}, noDialog=false }) => {
    const [visible, setVisible] = useState(false);
    const cardRef = useRef(null);


const makeAllVisibleAndResize = (node) => {
    let maxWidth = 0;

    const traverse = (element) => {
        const style = element.style;

        // Remove overflow restrictions
        style.overflow = 'visible';
        

        // Recurse through children
        Array.from(element.children).forEach(child => {
            if (child instanceof HTMLElement) {
                traverse(child);
            }
        });
    };

    traverse(node);
};

const takeScreenshot = async () => {
    if (cardRef.current) {
        const node = cardRef.current;
        node.id = "temp_ss_id";

        makeAllVisibleAndResize(node);

        try {
            const dataUrl = await toPng(node, {
                cacheBust: true,
                backgroundColor: 'white',
                pixelRatio: window.devicePixelRatio,
                width: node.scrollWidth,
                height: node.scrollHeight,
            });

            const link = document.createElement("a");
            link.download = `${title}.png`;
            link.href = dataUrl;
            link.click();
        } catch (error) {
            console.error('Screenshot failed:', error);
        }
    }
};



    if(!styleNow['width']) styleNow['width'] = '49%';
    return (
        <>
            <Card
                title={title}
                className="p-shadow-4 w3-center"
                style={styleNow ?? { overflow: 'hidden', borderRadius: '12px', width: '100%', maxWidth: '46vw', height: 'fit-content' }}
                onClick={() => setVisible(true)}
            >
                <div ref={(noDialog) ? cardRef : null} className='table-wrapper-with-black-text' style={{ padding: '1rem', width: '100%' }}>
                    {items}
                </div>
                {
                    (noDialog) ? (<Button label="Take Screenshot" icon="pi pi-camera" onClick={takeScreenshot} style={{ marginTop: '1rem' }} />) : null
                }
            </Card>
                {
                    (noDialog) ? null : (
                        <Dialog
                            header={title}
                            visible={visible}
                            style={{ width: '46vw', height: 'fit-content' }}
                            maximizable
                            onHide={() => setVisible(false)}
                            blockScroll={false}
                        >
                            <div ref={(noDialog) ? null : cardRef} className='table-wrapper-with-black-text' style={{ padding: '1rem' }}>
                                {items}
                                
                            </div>
                            <Button label="Take Screenshot" icon="pi pi-camera" onClick={takeScreenshot} style={{ marginTop: '1rem' }} />
                        </Dialog>
                    )
                }
            
        </>
    );
};

export default ChartCard;
