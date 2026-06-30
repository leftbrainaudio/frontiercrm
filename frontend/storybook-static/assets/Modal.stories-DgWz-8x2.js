import{s as e}from"./iframe-DL7Ge3lx.js";import{t}from"./react-a6xyYOoC.js";import{t as n}from"./jsx-runtime-Ccp0bkhE.js";import{t as r}from"./utils-BtRqtsxU.js";import{t as i}from"./x-CgXy7ZDH.js";import{t as a}from"./button-BOjjR3Vp.js";var o=e(t(),1),s=n(),c={sm:`max-w-sm`,md:`max-w-lg`,lg:`max-w-2xl`,xl:`max-w-4xl`,full:`max-w-[95vw] max-h-[95vh]`};function l({open:e,onClose:t,size:n=`md`,title:a,description:l,children:u,footer:d,className:f,closeOnBackdrop:p=!0,closeOnEscape:m=!0}){let h=(0,o.useRef)(null),g=(0,o.useRef)(null);(0,o.useEffect)(()=>{if(!e)return;g.current=document.activeElement,document.body.style.overflow=`hidden`;let t=setTimeout(()=>{h.current?.focus()},50);return()=>{clearTimeout(t),document.body.style.overflow=``,g.current?.focus()}},[e]);let _=(0,o.useCallback)(n=>{if(!(!e||!m)&&(n.key===`Escape`&&t(),n.key===`Tab`&&h.current)){let e=h.current.querySelectorAll(`button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])`);if(e.length===0)return;let t=e[0],r=e[e.length-1];n.shiftKey&&document.activeElement===t?(n.preventDefault(),r.focus()):!n.shiftKey&&document.activeElement===r&&(n.preventDefault(),t.focus())}},[e,m,t]);(0,o.useEffect)(()=>(document.addEventListener(`keydown`,_),()=>document.removeEventListener(`keydown`,_)),[_]);let v=(0,o.useCallback)(e=>{p&&e.target===e.currentTarget&&t()},[p,t]);return e?(0,s.jsxs)(`div`,{className:`fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4`,role:`dialog`,"aria-modal":`true`,"aria-labelledby":a?`modal-title`:void 0,"aria-describedby":l?`modal-desc`:void 0,children:[(0,s.jsx)(`div`,{className:`fixed inset-0 bg-black/50 backdrop-blur-sm animate-fade-in`,"aria-hidden":`true`,onClick:v}),(0,s.jsxs)(`div`,{ref:h,tabIndex:-1,className:r(`relative z-10 w-full rounded-t-xl sm:rounded-xl bg-white shadow-xl animate-slide-up`,`focus:outline-none`,`dark:bg-dark-surface dark:border dark:border-dark-border`,c[n],f),children:[(a||l)&&(0,s.jsxs)(`div`,{className:`flex items-start justify-between px-6 pt-6 pb-3`,children:[(0,s.jsxs)(`div`,{className:`flex-1 min-w-0 pr-4`,children:[a&&(0,s.jsx)(`h2`,{id:`modal-title`,className:`text-lg font-semibold text-text-primary dark:text-dark-text-primary`,children:a}),l&&(0,s.jsx)(`p`,{id:`modal-desc`,className:`mt-1 text-sm text-text-secondary dark:text-dark-text-secondary`,children:l})]}),(0,s.jsx)(`button`,{type:`button`,onClick:t,className:`shrink-0 rounded-lg p-1.5 text-text-tertiary hover:text-text-primary hover:bg-surface-secondary transition-colors dark:text-dark-text-tertiary dark:hover:text-dark-text-primary dark:hover:bg-dark-surface-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500`,"aria-label":`Close dialog`,children:(0,s.jsx)(i,{className:`h-5 w-5`})})]}),(0,s.jsx)(`div`,{className:r(`px-6 py-3 overflow-y-auto max-h-[60vh]`,!a&&`pt-6`),children:u}),d&&(0,s.jsx)(`div`,{className:`flex items-center justify-end gap-3 rounded-b-xl border-t border-border px-6 py-4 dark:border-dark-border`,children:d})]})]}):null}l.__docgenInfo={description:``,methods:[],displayName:`Modal`,props:{open:{required:!0,tsType:{name:`boolean`},description:`Whether the modal is open`},onClose:{required:!0,tsType:{name:`signature`,type:`function`,raw:`() => void`,signature:{arguments:[],return:{name:`void`}}},description:`Called when the modal should close`},size:{required:!1,tsType:{name:`union`,raw:`keyof typeof sizeStyles`,elements:[{name:`literal`,value:`sm`},{name:`literal`,value:`md`},{name:`literal`,value:`lg`},{name:`literal`,value:`xl`},{name:`literal`,value:`full`}]},description:`Dialog size`,defaultValue:{value:`'md'`,computed:!1}},title:{required:!1,tsType:{name:`string`},description:`Dialog title`},description:{required:!1,tsType:{name:`string`},description:`Optional description below the title`},children:{required:!0,tsType:{name:`ReactNode`},description:`Content of the modal body`},footer:{required:!1,tsType:{name:`ReactNode`},description:`Footer content (buttons etc)`},className:{required:!1,tsType:{name:`string`},description:`Additional className for the panel`},closeOnBackdrop:{required:!1,tsType:{name:`boolean`},description:`Whether clicking the backdrop calls onClose`,defaultValue:{value:`true`,computed:!1}},closeOnEscape:{required:!1,tsType:{name:`boolean`},description:`Whether pressing Escape calls onClose`,defaultValue:{value:`true`,computed:!1}}}};var u={title:`Atoms/Modal`,component:l,tags:[`autodocs`],argTypes:{size:{control:`select`,options:[`sm`,`md`,`lg`,`xl`,`full`]},closeOnBackdrop:{control:`boolean`},closeOnEscape:{control:`boolean`}}};function d(e){let[t,n]=(0,o.useState)(!1);return(0,s.jsxs)(s.Fragment,{children:[(0,s.jsx)(a,{onClick:()=>n(!0),children:`Open Modal`}),(0,s.jsx)(l,{open:t,onClose:()=>n(!1),...e})]})}var f={render:()=>(0,s.jsx)(d,{title:`Modal Title`,description:`This is a description for the modal dialog.`,children:(0,s.jsx)(`p`,{className:`text-sm text-gray-600 dark:text-gray-400`,children:`Modal content goes here. You can put any React components inside.`})})},p={render:()=>{let[e,t]=(0,o.useState)(!1);return(0,s.jsxs)(s.Fragment,{children:[(0,s.jsx)(a,{onClick:()=>t(!0),children:`Open with Footer`}),(0,s.jsx)(l,{open:e,onClose:()=>t(!1),title:`Confirm Action`,description:`Are you sure you want to proceed?`,footer:(0,s.jsxs)(s.Fragment,{children:[(0,s.jsx)(a,{variant:`ghost`,onClick:()=>t(!1),children:`Cancel`}),(0,s.jsx)(a,{onClick:()=>{t(!1),alert(`Confirmed!`)},children:`Confirm`})]}),children:(0,s.jsx)(`p`,{className:`text-sm text-gray-600 dark:text-gray-400`,children:`This action cannot be undone.`})})]})}},m={render:()=>(0,s.jsx)(`div`,{className:`flex flex-wrap gap-2`,children:[`sm`,`md`,`lg`,`xl`,`full`].map(e=>(0,s.jsx)(d,{size:e,title:`Size: ${e}`,children:(0,s.jsxs)(`p`,{className:`text-sm text-gray-600 dark:text-gray-400`,children:[`This modal uses the `,e,` size.`]})},e))})},h={render:()=>(0,s.jsx)(d,{title:`Simple Modal`,children:(0,s.jsx)(`p`,{className:`text-sm text-gray-600 dark:text-gray-400`,children:`This modal has no description, just a title.`})})};f.parameters={...f.parameters,docs:{...f.parameters?.docs,source:{originalSource:`{
  render: () => <ModalWrapper title="Modal Title" description="This is a description for the modal dialog.">
      <p className="text-sm text-gray-600 dark:text-gray-400">
        Modal content goes here. You can put any React components inside.
      </p>
    </ModalWrapper>
}`,...f.parameters?.docs?.source}}},p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
  render: () => {
    const [open, setOpen] = useState(false);
    return <>
        <Button onClick={() => setOpen(true)}>Open with Footer</Button>
        <Modal open={open} onClose={() => setOpen(false)} title="Confirm Action" description="Are you sure you want to proceed?" footer={<>
              <Button variant="ghost" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button onClick={() => {
          setOpen(false);
          alert('Confirmed!');
        }}>
                Confirm
              </Button>
            </>}>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            This action cannot be undone.
          </p>
        </Modal>
      </>;
  }
}`,...p.parameters?.docs?.source}}},m.parameters={...m.parameters,docs:{...m.parameters?.docs,source:{originalSource:`{
  render: () => <div className="flex flex-wrap gap-2">
      {(['sm', 'md', 'lg', 'xl', 'full'] as const).map(size => <ModalWrapper key={size} size={size} title={\`Size: \${size}\`}>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            This modal uses the {size} size.
          </p>
        </ModalWrapper>)}
    </div>
}`,...m.parameters?.docs?.source}}},h.parameters={...h.parameters,docs:{...h.parameters?.docs,source:{originalSource:`{
  render: () => <ModalWrapper title="Simple Modal">
      <p className="text-sm text-gray-600 dark:text-gray-400">
        This modal has no description, just a title.
      </p>
    </ModalWrapper>
}`,...h.parameters?.docs?.source}}};var g=[`Default`,`WithFooter`,`Sizes`,`NoDescription`];export{f as Default,h as NoDescription,m as Sizes,p as WithFooter,g as __namedExportsOrder,u as default};