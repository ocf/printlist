(function(){
    const RELOAD_TIME = 3000;
    let last_fetch = Date.now();
    setInterval(() => {
        loop(last_fetch).then(() => {
            last_fetch = Date.now();
        });
    }, RELOAD_TIME);
})();

async function loop(last_fetch){
    let data = await (await fetch(`/reload/recent?last-fetch=${last_fetch}`)).json();
    for (let printer_name in data){
        queue(printer_name, data[printer_name]);
    }
}

function element(username, date){
    let wrapper = document.createElement('div');
    wrapper.classList.add('printlist-user');
    let name = document.createElement('div');
    name.classList.add('printlist-user-handle');
    name.innerText = username;
    wrapper.appendChild(name);
    setTimeout(()=>wrapper.remove(), 180000)
    return wrapper;
}

function queue(printer_name, data){
    data.sort((a, b) => a[1]-b[1])
    .map(item => ([item[0], new Date(item[1]* 1000)]))
    .forEach(item => {
        let parent = document.querySelector(`.${printer_name} h1`);
        if (document.querySelector(`.${printer_name} .printlist-null`))
            document.querySelector(`.${printer_name} .printlist-null`).remove();
        parent.after(element(item[0], item[1]));
        // Do whatever you need, [username, date as Date Object]
    });
}