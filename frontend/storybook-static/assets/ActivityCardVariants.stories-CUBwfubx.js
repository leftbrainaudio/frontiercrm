import{t as e}from"./jsx-runtime-Ccp0bkhE.js";import{t}from"./activity-card-DLfpFykx.js";var n=e(),r={title:`Organisms/ActivityCard`,component:t,tags:[`autodocs`],parameters:{docs:{description:{component:`Displays a single timeline activity entry with type-specific icon, actor info, and entity link.`}}}};function i(e){return{id:`1`,activity_type:`note`,title:`Activity title`,description:`Activity description goes here.`,created_at:new Date().toISOString(),actor:{id:`u1`,name:`Alice Johnson`,avatar_url:``},entity:{id:`e1`,name:`Acme Corp`,url:`/contacts/e1`,type:`contact`},metadata:{},...e}}var a={render:()=>(0,n.jsx)(`div`,{className:`max-w-2xl`,children:(0,n.jsx)(t,{activity:i({})})})},o={render:()=>(0,n.jsx)(`div`,{className:`max-w-2xl`,children:[`note`,`email`,`meeting`,`call`,`task`,`deal_stage_change`,`deal_status_change`,`file_upload`,`system`].map(e=>(0,n.jsx)(t,{activity:i({id:e,activity_type:e,title:`${e.replace(/_/g,` `)} activity`,description:`This type has its own icon and color scheme.`})},e))})},s={render:()=>(0,n.jsx)(`div`,{className:`max-w-2xl`,children:(0,n.jsx)(t,{activity:i({activity_type:`note`,title:`Detailed call notes`,description:`During our hour-long discovery session, the client outlined their primary pain points including fragmented data across spreadsheets, lack of pipeline visibility for the sales team, and manual reporting that takes hours each week. They are evaluating CRM solutions with a decision expected by end of quarter. Key stakeholders include the VP of Sales, Head of Operations, and the IT director. Next steps include scheduling a technical deep-dive with their engineering team to review API integration requirements.`})})})};a.parameters={...a.parameters,docs:{...a.parameters?.docs,source:{originalSource:`{
  render: () => <div className="max-w-2xl">
      <ActivityCard activity={createActivity({})} />
    </div>
}`,...a.parameters?.docs?.source}}},o.parameters={...o.parameters,docs:{...o.parameters?.docs,source:{originalSource:`{
  render: () => {
    const types: TimelineEntry['activity_type'][] = ['note', 'email', 'meeting', 'call', 'task', 'deal_stage_change', 'deal_status_change', 'file_upload', 'system'];
    return <div className="max-w-2xl">
        {types.map(type => <ActivityCard key={type} activity={createActivity({
        id: type,
        activity_type: type,
        title: \`\${type.replace(/_/g, ' ')} activity\`,
        description: 'This type has its own icon and color scheme.'
      })} />)}
      </div>;
  }
}`,...o.parameters?.docs?.source}}},s.parameters={...s.parameters,docs:{...s.parameters?.docs,source:{originalSource:`{
  render: () => <div className="max-w-2xl">
      <ActivityCard activity={createActivity({
      activity_type: 'note',
      title: 'Detailed call notes',
      description: 'During our hour-long discovery session, the client outlined their primary pain points including fragmented data across spreadsheets, lack of pipeline visibility for the sales team, and manual reporting that takes hours each week. They are evaluating CRM solutions with a decision expected by end of quarter. Key stakeholders include the VP of Sales, Head of Operations, and the IT director. Next steps include scheduling a technical deep-dive with their engineering team to review API integration requirements.'
    })} />
    </div>
}`,...s.parameters?.docs?.source}}};var c=[`Overview`,`AllTypes`,`LongDescription`];export{o as AllTypes,s as LongDescription,a as Overview,c as __namedExportsOrder,r as default};