import{s as e}from"./iframe-DL7Ge3lx.js";import{t}from"./react-a6xyYOoC.js";import{t as n}from"./jsx-runtime-Ccp0bkhE.js";import{t as r}from"./utils-BtRqtsxU.js";import{t as i}from"./createLucideIcon-C1oJEDL8.js";import{t as a}from"./square-pen-D0juIiVH.js";import{t as o}from"./chevron-right-Cwsw31D3.js";import{t as s}from"./download-BcmW7mms.js";import{t as c}from"./trash-2-x1R1gc_l.js";import{t as l}from"./button-BOjjR3Vp.js";var u=i(`archive`,[[`rect`,{width:`20`,height:`5`,x:`2`,y:`3`,rx:`1`,key:`1wp1u1`}],[`path`,{d:`M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8`,key:`1s80jp`}],[`path`,{d:`M10 12h4`,key:`a56b0p`}]]),d=i(`copy`,[[`rect`,{width:`14`,height:`14`,x:`8`,y:`8`,rx:`2`,ry:`2`,key:`17jyea`}],[`path`,{d:`M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2`,key:`zix9uf`}]]),f=i(`share-2`,[[`circle`,{cx:`18`,cy:`5`,r:`3`,key:`gq8acd`}],[`circle`,{cx:`6`,cy:`12`,r:`3`,key:`w7nqdw`}],[`circle`,{cx:`18`,cy:`19`,r:`3`,key:`1xt0gg`}],[`line`,{x1:`8.59`,x2:`15.42`,y1:`13.51`,y2:`17.49`,key:`47mynk`}],[`line`,{x1:`15.41`,x2:`8.59`,y1:`6.51`,y2:`10.49`,key:`1n3mei`}]]),p=e(t(),1),m=n();function h({trigger:e,items:t,align:n=`start`,onOpenChange:i,open:a,className:s,...c}){let[l,u]=(0,p.useState)(!1),d=a!==void 0,f=d?a:l,h=(0,p.useRef)(null),g=(0,p.useRef)(null),_=(0,p.useRef)(-1),v=(0,p.useCallback)(e=>{d||u(e),i?.(e)},[d,i]);(0,p.useEffect)(()=>{if(!f)return;let e=e=>{h.current&&!h.current.contains(e.target)&&g.current&&!g.current.contains(e.target)&&v(!1)};return document.addEventListener(`mousedown`,e),()=>document.removeEventListener(`mousedown`,e)},[f,v]),(0,p.useEffect)(()=>{if(!f)return;let e=setTimeout(()=>{let e=h.current?.querySelectorAll(`[role="menuitem"]`);e&&e.length>0&&(e[0].focus(),_.current=0)},50);return()=>clearTimeout(e)},[f]),t.filter(e=>!e.divider);let y=e=>{let t=h.current?.querySelectorAll(`[role="menuitem"]:not([data-submenu])`);if(!t||t.length===0)return;let n=_.current;switch(e.key){case`ArrowDown`:e.preventDefault(),n=(n+1)%t.length;break;case`ArrowUp`:e.preventDefault(),n=(n-1+t.length)%t.length;break;case`Enter`:case` `:e.preventDefault(),t[n]?.click();return;case`Escape`:e.preventDefault(),v(!1),g.current?.focus();return;default:return}_.current=n,t[n]?.focus()},[b,x]=(0,p.useState)(null);return(0,m.jsxs)(`div`,{className:r(`relative inline-block`,s),...c,children:[(0,p.cloneElement)(e,{ref:g,onClick:t=>{t.stopPropagation(),e.props.onClick?.(),v(!f)},"aria-expanded":f,"aria-haspopup":`menu`}),f&&(0,m.jsx)(`div`,{ref:h,role:`menu`,tabIndex:-1,onKeyDown:y,className:r(`absolute z-50 mt-1 min-w-[200px] rounded-lg border border-border bg-white py-1 shadow-lg animate-fade-in dark:border-dark-border dark:bg-dark-surface`,n===`end`?`right-0`:`left-0`),children:t.map((e,t)=>{if(e.divider)return(0,m.jsx)(`div`,{className:`my-1 border-t border-border dark:border-dark-border`,role:`separator`},`divider-${t}`);let n=e.submenu&&e.submenu.length>0,i=b===t;return(0,m.jsxs)(`div`,{className:`relative`,children:[(0,m.jsxs)(`button`,{type:`button`,role:`menuitem`,disabled:e.disabled,"data-submenu":n?`true`:void 0,className:r(`flex w-full items-center gap-2.5 px-3 py-2 text-sm text-left transition-colors`,`focus-visible:outline-none focus-visible:bg-surface-secondary dark:focus-visible:bg-dark-surface-secondary`,`disabled:opacity-40 disabled:cursor-not-allowed`,e.danger?`text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20`:`text-text-primary dark:text-dark-text-primary hover:bg-surface-secondary dark:hover:bg-dark-surface-secondary`,e.className),onClick:()=>{n?x(i?null:t):(e.onClick?.(),v(!1))},onMouseEnter:()=>{n&&x(t)},onMouseLeave:()=>{n&&x(null)},children:[e.icon&&(0,m.jsx)(`span`,{className:`shrink-0 h-4 w-4 text-text-tertiary dark:text-dark-text-tertiary`,children:e.icon}),(0,m.jsx)(`span`,{className:`flex-1`,children:e.label}),n&&(0,m.jsx)(o,{className:`h-3.5 w-3.5 text-text-tertiary dark:text-dark-text-tertiary`})]}),n&&i&&(0,m.jsx)(`div`,{role:`menu`,className:r(`absolute top-0 left-full ml-1 min-w-[180px] rounded-lg border border-border bg-white py-1 shadow-lg dark:border-dark-border dark:bg-dark-surface`),children:e.submenu.map(e=>(0,m.jsxs)(`button`,{type:`button`,role:`menuitem`,disabled:e.disabled,className:r(`flex w-full items-center gap-2.5 px-3 py-2 text-sm text-left transition-colors`,`focus-visible:outline-none focus-visible:bg-surface-secondary dark:focus-visible:bg-dark-surface-secondary`,`disabled:opacity-40 disabled:cursor-not-allowed`,e.danger?`text-red-600 dark:text-red-400`:`text-text-primary dark:text-dark-text-primary`,`hover:bg-surface-secondary dark:hover:bg-dark-surface-secondary`),onClick:()=>{e.onClick?.(),v(!1)},children:[e.icon&&(0,m.jsx)(`span`,{className:`shrink-0 h-4 w-4 text-text-tertiary dark:text-dark-text-tertiary`,children:e.icon}),e.label]},e.label))})]},e.label)})})]})}h.__docgenInfo={description:``,methods:[],displayName:`Dropdown`,props:{trigger:{required:!0,tsType:{name:`ReactElement`,elements:[{name:`signature`,type:`object`,raw:`{ onClick?: () => void; ref?: React.Ref<unknown> }`,signature:{properties:[{key:`onClick`,value:{name:`signature`,type:`function`,raw:`() => void`,signature:{arguments:[],return:{name:`void`}},required:!1}},{key:`ref`,value:{name:`ReactRef`,raw:`React.Ref<unknown>`,elements:[{name:`unknown`}],required:!1}}]}}],raw:`ReactElement<{ onClick?: () => void; ref?: React.Ref<unknown> }>`},description:`The trigger element`},items:{required:!0,tsType:{name:`Array`,elements:[{name:`DropdownItem`}],raw:`DropdownItem[]`},description:`Menu items`},align:{required:!1,tsType:{name:`union`,raw:`'start' | 'end'`,elements:[{name:`literal`,value:`'start'`},{name:`literal`,value:`'end'`}]},description:`Menu alignment relative to trigger`,defaultValue:{value:`'start'`,computed:!1}},onOpenChange:{required:!1,tsType:{name:`signature`,type:`function`,raw:`(open: boolean) => void`,signature:{arguments:[{type:{name:`boolean`},name:`open`}],return:{name:`void`}}},description:`Called when menu opens/closes`},open:{required:!1,tsType:{name:`boolean`},description:`Controlled open state`}},composes:[`HTMLAttributes`]};var g={title:`Molecules/Dropdown`,component:h,tags:[`autodocs`],argTypes:{align:{control:`select`,options:[`start`,`end`]}}},_={args:{trigger:(0,m.jsx)(l,{variant:`secondary`,children:`Actions`}),items:[{label:`Edit`,onClick:()=>alert(`Edit`)},{label:`Copy`,onClick:()=>alert(`Copy`)},{label:`Delete`,onClick:()=>alert(`Delete`)}]}},v={args:{trigger:(0,m.jsx)(l,{variant:`secondary`,children:`Actions`}),items:[{label:`Edit`,icon:(0,m.jsx)(a,{className:`h-4 w-4`}),onClick:()=>alert(`Edit`)},{label:`Duplicate`,icon:(0,m.jsx)(d,{className:`h-4 w-4`}),onClick:()=>alert(`Duplicate`)},{label:`Share`,icon:(0,m.jsx)(f,{className:`h-4 w-4`}),onClick:()=>alert(`Share`)}]}},y={args:{trigger:(0,m.jsx)(l,{variant:`secondary`,children:`More`}),items:[{label:`Edit`,icon:(0,m.jsx)(a,{className:`h-4 w-4`}),onClick:()=>alert(`Edit`)},{label:`Duplicate`,icon:(0,m.jsx)(d,{className:`h-4 w-4`}),onClick:()=>alert(`Duplicate`)},{label:``,divider:!0},{label:`Export`,icon:(0,m.jsx)(s,{className:`h-4 w-4`}),onClick:()=>alert(`Export`)},{label:``,divider:!0},{label:`Archive`,icon:(0,m.jsx)(u,{className:`h-4 w-4`}),onClick:()=>alert(`Archive`)},{label:`Delete`,icon:(0,m.jsx)(c,{className:`h-4 w-4`}),danger:!0,onClick:()=>alert(`Delete`)}]}},b={render:()=>(0,m.jsx)(`div`,{className:`flex justify-end`,children:(0,m.jsx)(h,{align:`end`,trigger:(0,m.jsx)(l,{variant:`secondary`,children:`End Aligned`}),items:[{label:`Option A`},{label:`Option B`},{label:`Option C`}]})})},x={args:{trigger:(0,m.jsx)(l,{variant:`secondary`,children:`File`}),items:[{label:`New File`,icon:(0,m.jsx)(a,{className:`h-4 w-4`})},{label:`Export As`,icon:(0,m.jsx)(s,{className:`h-4 w-4`}),submenu:[{label:`PDF`,onClick:()=>alert(`Export as PDF`)},{label:`CSV`,onClick:()=>alert(`Export as CSV`)},{label:`JSON`,onClick:()=>alert(`Export as JSON`)}]},{label:``,divider:!0},{label:`Delete`,icon:(0,m.jsx)(c,{className:`h-4 w-4`}),danger:!0}]}};_.parameters={..._.parameters,docs:{..._.parameters?.docs,source:{originalSource:`{
  args: {
    trigger: <Button variant="secondary">Actions</Button>,
    items: [{
      label: 'Edit',
      onClick: () => alert('Edit')
    }, {
      label: 'Copy',
      onClick: () => alert('Copy')
    }, {
      label: 'Delete',
      onClick: () => alert('Delete')
    }]
  }
}`,..._.parameters?.docs?.source}}},v.parameters={...v.parameters,docs:{...v.parameters?.docs,source:{originalSource:`{
  args: {
    trigger: <Button variant="secondary">Actions</Button>,
    items: [{
      label: 'Edit',
      icon: <Edit className="h-4 w-4" />,
      onClick: () => alert('Edit')
    }, {
      label: 'Duplicate',
      icon: <Copy className="h-4 w-4" />,
      onClick: () => alert('Duplicate')
    }, {
      label: 'Share',
      icon: <Share2 className="h-4 w-4" />,
      onClick: () => alert('Share')
    }]
  }
}`,...v.parameters?.docs?.source}}},y.parameters={...y.parameters,docs:{...y.parameters?.docs,source:{originalSource:`{
  args: {
    trigger: <Button variant="secondary">More</Button>,
    items: [{
      label: 'Edit',
      icon: <Edit className="h-4 w-4" />,
      onClick: () => alert('Edit')
    }, {
      label: 'Duplicate',
      icon: <Copy className="h-4 w-4" />,
      onClick: () => alert('Duplicate')
    }, {
      label: '',
      divider: true
    }, {
      label: 'Export',
      icon: <Download className="h-4 w-4" />,
      onClick: () => alert('Export')
    }, {
      label: '',
      divider: true
    }, {
      label: 'Archive',
      icon: <Archive className="h-4 w-4" />,
      onClick: () => alert('Archive')
    }, {
      label: 'Delete',
      icon: <Trash2 className="h-4 w-4" />,
      danger: true,
      onClick: () => alert('Delete')
    }]
  }
}`,...y.parameters?.docs?.source}}},b.parameters={...b.parameters,docs:{...b.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex justify-end">
      <Dropdown align="end" trigger={<Button variant="secondary">End Aligned</Button>} items={[{
      label: 'Option A'
    }, {
      label: 'Option B'
    }, {
      label: 'Option C'
    }]} />
    </div>
}`,...b.parameters?.docs?.source}}},x.parameters={...x.parameters,docs:{...x.parameters?.docs,source:{originalSource:`{
  args: {
    trigger: <Button variant="secondary">File</Button>,
    items: [{
      label: 'New File',
      icon: <Edit className="h-4 w-4" />
    }, {
      label: 'Export As',
      icon: <Download className="h-4 w-4" />,
      submenu: [{
        label: 'PDF',
        onClick: () => alert('Export as PDF')
      }, {
        label: 'CSV',
        onClick: () => alert('Export as CSV')
      }, {
        label: 'JSON',
        onClick: () => alert('Export as JSON')
      }]
    }, {
      label: '',
      divider: true
    }, {
      label: 'Delete',
      icon: <Trash2 className="h-4 w-4" />,
      danger: true
    }]
  }
}`,...x.parameters?.docs?.source}}};var S=[`Default`,`WithIcons`,`WithDividers`,`AlignEnd`,`WithSubmenu`];export{b as AlignEnd,_ as Default,y as WithDividers,v as WithIcons,x as WithSubmenu,S as __namedExportsOrder,g as default};