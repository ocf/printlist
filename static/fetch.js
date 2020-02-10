const RELOAD_TIME = 3000; 
const PERSISTENCE_TIME = 180000;

class Job {
    constructor(parent, printer_name, username, date) {
        this.date = new Date(date*1000);
        this.parent = parent;
        this.printer_name = printer_name;
        this.username = username;
        this.element = this.createElement();
        this.symbol = Symbol();
    }
    createElement(){
        let wrapper = document.createElement('div');
        wrapper.classList.add('printlist-user');
        let name = document.createElement('div');
        name.classList.add('printlist-user-handle');
        name.innerText = this.username;
        wrapper.appendChild(name);
        return wrapper;
    }
    remove(){
        this.parent.printers[this.printer_name].delete(this.symbol);
        if (this.element) {
            this.element.remove();
            delete this.element;
        }

    }
}

class AutoReload {
    constructor(){
        this.printers;
        this.last_fetch = 0;
        this.update(this.last_fetch);
        setInterval(()=>this.update(this.last_fetch), RELOAD_TIME);
    }
    async update(last_fetch = 0){
        console.log(last_fetch);
        let data = await (await fetch(`/reload/recent?last-fetch=${last_fetch}`)).json();
        this.last_fetch = Date.now();
        if (!this.printers) {
            this.printers = {};
            for (let printer_name in data) {
                this.printers[printer_name] = new Map();
            }
        }
        let currTime = Date.now();
        for (let printer_name in data) {
            let parent = document.querySelector(`.${printer_name} h1`);
            data[printer_name].sort((a, b) => a[1] - b[1])
            .forEach(item=>{
                let job = new Job(this, printer_name, item[0], item[1]);
                this.printers[printer_name].set(job.symbol, job);
                parent.after(job.element);
            });
            this.printers[printer_name].forEach(job => {
                if (currTime - job.date.getTime() > PERSISTENCE_TIME)
                    job.remove();
            });
            if (this.printers[printer_name].size == 0) {
                if (!document.querySelector(`.${printer_name} .printlist-null`))
                    parent.after(this.createNull());
            }
            else
                this.deleteNull(printer_name);
        }
    }
    createNull(){
        let nullDiv = document.createElement('div');
        nullDiv.classList.add('printlist-null');
        nullDiv.innerText = '(there are no jobs printing)';
        return nullDiv;
    }
    deleteNull(printer_name){
        let target = document.querySelector(`.${printer_name} .printlist-null`);
        if (target)
            target.remove();
    }
}

(function(){
    new AutoReload();
}());