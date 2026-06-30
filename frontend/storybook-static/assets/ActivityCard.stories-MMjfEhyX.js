import{t as e}from"./activity-card-DLfpFykx.js";var t={id:`1`,activity_type:`note`,title:`Follow-up call completed`,description:`Discussed next quarter plans and budget allocation. Client expressed interest in enterprise tier.`,created_at:new Date().toISOString(),actor:{id:`u1`,name:`Alice Johnson`,avatar_url:``},entity:{id:`e1`,name:`Acme Corp`,url:`/contacts/e1`,type:`contact`},metadata:{}},n={title:`Organisms/ActivityCard`,component:e,tags:[`autodocs`]},r={args:{activity:t}},i={args:{activity:{...t,activity_type:`email`,title:`Proposal sent`,description:`Sent Q3 proposal with pricing breakdown and implementation timeline.`}}},a={args:{activity:{...t,activity_type:`meeting`,title:`Product demo`,description:`Demonstrated new features including pipeline forecasting and CSV export.`}}},o={args:{activity:{...t,activity_type:`deal_stage_change`,title:`Deal moved to Negotiation`,description:`Deal progressed from Proposal to Negotiation stage.`}}},s={args:{activity:{...t,activity_type:`call`,title:`Discovery call`,description:`Initial call with prospect to understand requirements.`}}},c={args:{activity:{...t,actor:{id:`system`,name:``,avatar_url:``}}}},l={args:{activity:{...t,entity:{id:``,name:``,url:``,type:``}}}};r.parameters={...r.parameters,docs:{...r.parameters?.docs,source:{originalSource:`{
  args: {
    activity: sampleActivity
  }
}`,...r.parameters?.docs?.source}}},i.parameters={...i.parameters,docs:{...i.parameters?.docs,source:{originalSource:`{
  args: {
    activity: {
      ...sampleActivity,
      activity_type: 'email',
      title: 'Proposal sent',
      description: 'Sent Q3 proposal with pricing breakdown and implementation timeline.'
    }
  }
}`,...i.parameters?.docs?.source}}},a.parameters={...a.parameters,docs:{...a.parameters?.docs,source:{originalSource:`{
  args: {
    activity: {
      ...sampleActivity,
      activity_type: 'meeting',
      title: 'Product demo',
      description: 'Demonstrated new features including pipeline forecasting and CSV export.'
    }
  }
}`,...a.parameters?.docs?.source}}},o.parameters={...o.parameters,docs:{...o.parameters?.docs,source:{originalSource:`{
  args: {
    activity: {
      ...sampleActivity,
      activity_type: 'deal_stage_change',
      title: 'Deal moved to Negotiation',
      description: 'Deal progressed from Proposal to Negotiation stage.'
    }
  }
}`,...o.parameters?.docs?.source}}},s.parameters={...s.parameters,docs:{...s.parameters?.docs,source:{originalSource:`{
  args: {
    activity: {
      ...sampleActivity,
      activity_type: 'call',
      title: 'Discovery call',
      description: 'Initial call with prospect to understand requirements.'
    }
  }
}`,...s.parameters?.docs?.source}}},c.parameters={...c.parameters,docs:{...c.parameters?.docs,source:{originalSource:`{
  args: {
    activity: {
      ...sampleActivity,
      actor: {
        id: 'system',
        name: '',
        avatar_url: ''
      }
    }
  }
}`,...c.parameters?.docs?.source}}},l.parameters={...l.parameters,docs:{...l.parameters?.docs,source:{originalSource:`{
  args: {
    activity: {
      ...sampleActivity,
      entity: {
        id: '',
        name: '',
        url: '',
        type: ''
      }
    }
  }
}`,...l.parameters?.docs?.source}}};var u=[`Default`,`EmailActivity`,`MeetingActivity`,`DealStageChange`,`CallActivity`,`NoActor`,`NoEntity`];export{s as CallActivity,o as DealStageChange,r as Default,i as EmailActivity,a as MeetingActivity,c as NoActor,l as NoEntity,u as __namedExportsOrder,n as default};