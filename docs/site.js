(function(){
var p=document.querySelector('.progress'),a=document.querySelector('article.piece');
if(p&&a){var queued=false,update=function(){queued=false;var r=a.getBoundingClientRect(),h=r.height-innerHeight;
p.style.setProperty('--p',Math.min(1,Math.max(0,h>0?-r.top/h:1)).toFixed(4));};
addEventListener('scroll',function(){if(!queued){queued=true;requestAnimationFrame(update);}},{passive:true});
addEventListener('resize',update);update();}
})();