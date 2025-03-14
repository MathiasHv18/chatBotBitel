import React from 'react'
import './Chats.css'
function Chats() {
    const tables_names=[
        { name: 'DISCOUNTS', description: 'Contains details about discount offers.' },
        { name: 'COMPLAINTS', description: 'Logs customer complaints.' },
        { name: 'MIGRATION', description: 'Tracks customer migrations.' },
        { name: 'CUST_AGE', description: 'Contains customer demographic details.' },
        { name: 'ISDN_DETAILS', description: 'Customer subscription details.' },
        { name: 'CONST_DETAILS', description: 'Records customer usage data.' },
        { name: 'PACKAGES', description: 'Logs purchased packages.' },
        { name: 'PAYMENT', description: 'Details on customer payments.' },
        { name: 'REFILLS', description: 'Tracks customer refills.' },
        { name: 'OFFER_PRODUCTS', description: 'Lists available product offers.' }
    ];

    const handleTableClick = (tableName) => {
        console.log(`Selected table: ${tableName}`);
    };

    return (
        <div className="chat-history">
            <h1>BITEL CHAT BOT</h1>
            <h2>You want specific table information?</h2>
            <div className="buttons-container">
                {tables_names.map((table, index) => (
                    <button 
                        key={index} 
                        className="table-button" 
                        onClick={() => handleTableClick(table.name)}
                    >
                        {table.name} <br /> {table.description}
                    </button>
                ))}
            </div>
        </div>
  )
}

export default Chats