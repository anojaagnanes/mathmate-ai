/** Page-local cache: no images, credentials or text written to persistent storage. */
export class WorkOcrCache {
  private entries = new Map<string, {text:string; confirmed:boolean}>();
  async key(image: Blob): Promise<string> {
    const digest=await crypto.subtle.digest('SHA-256',await image.arrayBuffer());
    return Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('');
  }
  get(key:string){return this.entries.get(key);}
  remove(key:string){this.entries.delete(key);}
  set(key:string,text:string,confirmed=false){
    if(!key||!text.trim())return;
    if(!this.entries.has(key)&&this.entries.size>=5)this.entries.delete(this.entries.keys().next().value!);
    this.entries.set(key,{text,confirmed});
  }
}
