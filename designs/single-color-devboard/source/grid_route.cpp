#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <queue>
#include <string>
#include <vector>

struct Entry { uint32_t f,g,id; bool operator<(const Entry& o) const {return f>o.f || (f==o.f && g<o.g);} };
int main(int argc,char** argv) {
    if(argc!=2) return 2;
    std::string root=argv[1];
    std::ifstream input(root+".points");
    int w,h,ns,ng; input>>w>>h>>ns>>ng;
    if(!input || ns<1 || ng<1) return 2;
    const uint32_t n=w*h,total=4*n,inf=std::numeric_limits<uint32_t>::max();
    std::vector<uint8_t> blocked(total),vias(n),goal(total,0);
    std::ifstream(root+".maps",std::ios::binary).read((char*)blocked.data(),total);
    std::ifstream(root+".vias",std::ios::binary).read((char*)vias.data(),n);
    std::vector<uint32_t> starts;
    for(int i=0;i<ns;i++) {int z,x,y;input>>z>>x>>y; auto id=z*n+y*w+x; if(!blocked[id]) starts.push_back(id);}
    int x0=w,x1=0,y0=h,y1=0;
    int goals=0;
    for(int i=0;i<ng;i++) {
        int z,x,y;input>>z>>x>>y;auto id=z*n+y*w+x;
        if(!blocked[id]) {goal[id]=1;goals++;x0=std::min(x0,x);x1=std::max(x1,x);y0=std::min(y0,y);y1=std::max(y1,y);}
    }
    if(starts.empty() || !goals) {std::cout<<"Blocked endpoints\n";return 3;}
    auto heuristic=[&](uint32_t id) {
        int p=id%n,x=p%w,y=p/w;
        int dx=std::max({x0-x,x-x1,0}),dy=std::max({y0-y,y-y1,0});
        return (uint32_t)(10*std::max(dx,dy)+4*std::min(dx,dy));
    };
    std::vector<uint32_t> cost(total,inf),parent(total,inf);
    std::vector<uint8_t> heading(total,8);
    std::priority_queue<Entry> queue;
    for(auto id:starts) {cost[id]=0;parent[id]=id;queue.push({heuristic(id),0,id});}
    uint32_t found=inf;uint64_t expanded=0;
    const int dx[8]={1,-1,0,0,1,1,-1,-1},dy[8]={0,0,1,-1,1,-1,1,-1};
    auto visit=[&](uint32_t next,uint32_t current,uint32_t value,uint8_t direction) {
        if(!blocked[next] && value<cost[next]) {
            cost[next]=value;parent[next]=current;heading[next]=direction;
            queue.push({value+heuristic(next),value,next});
        }
    };
    while(!queue.empty()) {
        auto e=queue.top();queue.pop();if(e.g!=cost[e.id]) continue;
        if(goal[e.id]) {found=e.id;break;}
        if(++expanded>50000000) break;
        const int z=e.id/n,p=e.id%n,x=p%w,y=p/w;
        for(int i=0;i<8;i++) {
            int xx=x+dx[i],yy=y+dy[i];
            if(xx<0||xx>=w||yy<0||yy>=h) continue;
            if(i>=4 && (blocked[z*n+y*w+xx] || blocked[z*n+yy*w+x])) continue;
            visit(z*n+yy*w+xx,e.id,e.g+(i<4?10:14)+(heading[e.id]!=8 && heading[e.id]!=i?120:0),i);
        }
        if(!vias[p]) for(int zz=0;zz<4;zz++) if(zz!=z) visit(zz*n+p,e.id,e.g+1200,8);
    }
    if(found==inf) {std::cout<<"No path after "<<expanded<<" expansions\n";return 4;}
    std::vector<uint32_t> path;
    for(auto id=found;;id=parent[id]) {path.push_back(id);if(parent[id]==id) break;}
    std::reverse(path.begin(),path.end());
    std::ofstream output(root+".path");output<<path.size()<<"\n";
    for(auto id:path) output<<id/n<<" "<<(id%n)%w<<" "<<(id%n)/w<<"\n";
    std::cout<<"Path "<<path.size()<<" nodes, "<<expanded<<" expansions, cost "<<cost[found]<<"\n";
}
