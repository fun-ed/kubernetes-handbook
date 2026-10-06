> HISTORICAL: This analysis describes old etcd internals and commands. Do not use it as current operational guidance.

# etcd

Etcd 是 CoreOS 基於 Raft 開發的分散式 key-value 儲存，可用於服務發現、共享設定以及一致性保障（如資料庫選主、分散式鎖等）。

## Etcd 主要功能

* 基本的 key-value 儲存
* 監聽機制
* key 的過期及續約機制，用於監控和服務發現
* 原子 CAS 和 CAD，用於分散式鎖和 leader 選舉

## Etcd 基於 RAFT 的一致性

選舉方法

* 1\) 初始啟動時，節點處於 follower 狀態並被設定一個 election timeout，如果在這一時間週期內沒有收到來自 leader 的 heartbeat，節點將發起選舉：將自己切換為 candidate 之後，向叢集中其它 follower 節點傳送請求，詢問其是否選舉自己成為 leader。
* 2\) 當收到來自叢集中過半數節點的接受投票後，節點即成為 leader，開始接收儲存 client 的資料並向其它的 follower 節點同步日誌。如果沒有達成一致，則 candidate 隨機選擇一個等待間隔（150ms ~ 300ms）再次發起投票，得到叢集中半數以上 follower 接受的 candidate 將成為 leader
* 3\) leader 節點依靠定時向 follower 傳送 heartbeat 來保持其地位。
* 4\) 任何時候如果其它 follower 在 election timeout 期間都沒有收到來自 leader 的 heartbeat，同樣會將自己的狀態切換為 candidate 併發起選舉。每成功選舉一次，新 leader 的任期（Term）都會比之前 leader 的任期大 1。

日誌複製

當前 Leader 收到客戶端的日誌（事務請求）後先把該日誌追加到本地的 Log 中，然後透過 heartbeat 把該 Entry 同步給其他 Follower，Follower 接收到日誌後記錄日誌然後向 Leader 傳送 ACK，當 Leader 收到大多數（n/2+1）Follower 的 ACK 資訊後將該日誌設定為已提交併追加到本地磁碟中，通知客戶端並在下個 heartbeat 中 Leader 將通知所有的 Follower 將該日誌儲存在自己的本地磁碟中。

安全性

安全性是用於保證每個節點都執行相同序列的安全機制，如當某個 Follower 在當前 Leader commit Log 時變得不可用了，稍後可能該 Follower 又會被選舉為 Leader，這時新 Leader 可能會用新的 Log 覆蓋先前已 committed 的 Log，這就是導致節點執行不同序列；Safety 就是用於保證選舉出來的 Leader 一定包含先前 committed Log 的機制；

* 選舉安全性（Election Safety）：每個任期（Term）只能選舉出一個 Leader
* Leader 完整性（Leader Completeness）：指 Leader 日誌的完整性，當 Log 在任期 Term1 被 Commit 後，那麼以後任期 Term2、Term3… 等的 Leader 必須包含該 Log；Raft 在選舉階段就使用 Term 的判斷用於保證完整性：當請求投票的該 Candidate 的 Term 較大或 Term 相同 Index 更大則投票，否則拒絕該請求。

失效處理

* 1\) Leader 失效：其他沒有收到 heartbeat 的節點會發起新的選舉，而當 Leader 恢復後由於步進數小會自動成為 follower（日誌也會被新 leader 的日誌覆蓋）
* 2）follower 節點不可用：follower 節點不可用的情況相對容易解決。因為叢集中的日誌內容始終是從 leader 節點同步的，只要這一節點再次加入叢集時重新從 leader 節點處複製日誌即可。
* 3）多個 candidate：衝突後 candidate 將隨機選擇一個等待間隔（150ms ~ 300ms）再次發起投票，得到叢集中半數以上 follower 接受的 candidate 將成為 leader

### wal 日誌

Etcd 實現 raft 的時候，充分利用了 go 語言 CSP 併發模型和 chan 的魔法，想更進行一步瞭解的可以去看原始碼，這裡只簡單分析下它的 wal 日誌。

![etcdv3](https://github.com/fun-ed/kubernetes-handbook/blob/main/.gitbook/assets/etcd-log%20%281%29.png)

wal 日誌是二進位制的，解析出來後是以上資料結構 LogEntry。其中第一個欄位 type，只有兩種，一種是 0 表示 Normal，1 表示 ConfChange（ConfChange 表示 Etcd 本身的設定變更同步，比如有新的節點加入等）。第二個欄位是 term，每個 term 代表一個主節點的任期，每次主節點變更 term 就會變化。第三個欄位是 index，這個序號是嚴格有序遞增的，代表變更序號。第四個欄位是二進位制的 data，將 raft request 物件的 pb 結構整個儲存下。Etcd 原始碼下有個 tools/etcd-dump-logs，可以將 wal 日誌 dump 成文字檢視，可以協助分析 raft 協議。

raft 協議本身不關心應用資料，也就是 data 中的部分，一致性都透過同步 wal 日誌來實現，每個節點將從主節點收到的 data apply 到本地的儲存，raft 只關心日誌的同步狀態，如果本地儲存實現的有 bug，比如沒有正確的將 data apply 到本地，也可能會導致資料不一致。

## Etcd v2 與 v3

Etcd v2 和 v3 本質上是共享同一套 raft 協議程式碼的兩個獨立的應用，介面不一樣，儲存不一樣，資料互相隔離。也就是說如果從 Etcd v2 升級到 Etcd v3，原來 v2 的資料還是隻能用 v2 的介面存取，v3 的介面建立的資料也只能存取透過 v3 的介面存取。所以我們按照 v2 和 v3 分別分析。

推薦在 Kubernetes 叢集中使用 **Etcd v3**，**v2 版本已在 Kubernetes v1.11 中棄用**。

## Etcd v2 儲存，Watch 以及過期機制

![etcdv2](https://github.com/fun-ed/kubernetes-handbook/blob/main/.gitbook/assets/etcd-v2%20%281%29.png)

Etcd v2 是個純記憶體的實現，並未實時將資料寫入到磁碟，持久化機制很簡單，就是將 store 整合序列化成 json 寫入檔案。資料在記憶體中是一個簡單的樹結構。比如以下資料儲存到 Etcd 中的結構就如圖所示。

```text
/nodes/1/name  node1
/nodes/1/ip    192.168.1.1
```

store 中有一個全域性的 currentIndex，每次變更，index 會加 1. 然後每個 event 都會關聯到 currentIndex.

當客戶端呼叫 watch 介面（引數中增加 wait 引數）時，如果請求引數中有 waitIndex，並且 waitIndex 小於 currentIndex，則從 EventHistroy 表中查詢 index 大於等於 waitIndex，並且和 watch key 匹配的 event，如果有資料，則直接返回。如果歷史表中沒有或者請求沒有帶 waitIndex，則放入 WatchHub 中，每個 key 會關聯一個 watcher 列表。 當有變更操作時，變更生成的 event 會放入 EventHistroy 表中，同時通知和該 key 相關的 watcher。

這裡有幾個影響使用的細節問題：

1. EventHistroy 是有長度限制的，最長 1000。也就是說，如果你的客戶端停了許久，然後重新 watch 的時候，可能和該 waitIndex 相關的 event 已經被淘汰了，這種情況下會丟失變更。
2. 如果通知 watcher 的時候，出現了阻塞（每個 watcher 的 channel 有 100 個緩衝空間），Etcd 會直接把 watcher 刪除，也就是會導致 wait 請求的連線中斷，客戶端需要重新連線。
3. Etcd store 的每個 node 中都儲存了過期時間，透過定時機制進行清理。

從而可以看出，Etcd v2 的一些限制：

1. 過期時間只能設定到每個 key 上，如果多個 key 要保證生命週期一致則比較困難。
2. watcher 只能 watch 某一個 key 以及其子節點（透過引數 recursive\)，不能進行多個 watch。
3. 很難透過 watch 機制來實現完整的資料同步（有丟失變更的風險），所以當前的大多數使用方式是透過 watch 得知變更，然後透過 get 重新獲取資料，並不完全依賴於 watch 的變更 event。

## Etcd v3 儲存，Watch 以及過期機制

![etcdv3](https://github.com/fun-ed/kubernetes-handbook/blob/main/.gitbook/assets/etcd-v3%20%281%29.png)

Etcd v3 將 watch 和 store 拆開實現，我們先分析下 store 的實現。

Etcd v3 store 分為兩部分，一部分是記憶體中的索引，kvindex，是基於 google 開源的一個 golang 的 btree 實現的，另外一部分是後端儲存。按照它的設計，backend 可以對接多種儲存，當前使用的 boltdb。boltdb 是一個單機的支援事務的 kv 儲存，Etcd 的事務是基於 boltdb 的事務實現的。Etcd 在 boltdb 中儲存的 key 是 revision，value 是 Etcd 自己的 key-value 組合，也就是說 Etcd 會在 boltdb 中把每個版本都儲存下，從而實現了多版本機制。

舉個例子： 用 etcdctl 透過批次介面寫入兩條記錄：

```text
etcdctl txn <<<'
put key1 "v1"
put key2 "v2"

'
```

再透過批次介面更新這兩條記錄：

```text
etcdctl txn <<<'
put key1 "v12"
put key2 "v22"

'
```

boltdb 中其實有了 4 條資料：

```text
rev={3 0}, key=key1, value="v1"
rev={3 1}, key=key2, value="v2"
rev={4 0}, key=key1, value="v12"
rev={4 1}, key=key2, value="v22"
```

revision 主要由兩部分組成，第一部分 main rev，每次事務進行加一，第二部分 sub rev，同一個事務中的每次操作加一。如上範例，第一次操作的 main rev 是 3，第二次是 4。當然這種機制大家想到的第一個問題就是空間問題，所以 Etcd 提供了命令和設定選項來控制 compact，同時支援 put 操作的引數來精確控制某個 key 的歷史版本數。

瞭解了 Etcd 的磁碟儲存，可以看出如果要從 boltdb 中查詢資料，必須透過 revision，但客戶端都是透過 key 來查詢 value，所以 Etcd 的記憶體 kvindex 儲存的就是 key 和 revision 之前的對映關係，用來加速查詢。

然後我們再分析下 watch 機制的實現。Etcd v3 的 watch 機制支援 watch 某個固定的 key，也支援 watch 一個範圍（可以用於模擬目錄的結構的 watch），所以 watchGroup 包含兩種 watcher，一種是 key watchers，資料結構是每個 key 對應一組 watcher，另外一種是 range watchers, 資料結構是一個 IntervalTree（不熟悉的參看文文末連結），方便透過區間查詢到對應的 watcher。

同時，每個 WatchableStore 包含兩種 watcherGroup，一種是 synced，一種是 unsynced，前者表示該 group 的 watcher 資料都已經同步完畢，在等待新的變更，後者表示該 group 的 watcher 資料同步落後於當前最新變更，還在追趕。

當 Etcd 收到客戶端的 watch 請求，如果請求攜帶了 revision 引數，則比較請求的 revision 和 store 當前的 revision，如果大於當前 revision，則放入 synced 組中，否則放入 unsynced 組。同時 Etcd 會啟動一個後臺的 goroutine 持續同步 unsynced 的 watcher，然後將其遷移到 synced 組。也就是這種機制下，Etcd v3 支援從任意版本開始 watch，沒有 v2 的 1000 條歷史 event 表限制的問題（當然這是指沒有 compact 的情況下）。

另外我們前面提到的，Etcd v2 在通知客戶端時，如果網路不好或者客戶端讀取比較慢，發生了阻塞，則會直接關閉當前連線，客戶端需要重新發起請求。Etcd v3 為了解決這個問題，專門維護了一個推送時阻塞的 watcher 佇列，在另外的 goroutine 裡進行重試。

Etcd v3 對過期機制也做了改進，過期時間設定在 lease 上，然後 key 和 lease 關聯。這樣可以實現多個 key 關聯同一個 lease id，方便設定統一的過期時間，以及實現批次續約。

相比 Etcd v2, Etcd v3 的一些主要變化：

1. 介面透過 grpc 提供 rpc 介面，放棄了 v2 的 http 介面。優勢是長連線效率提升明顯，缺點是使用不如以前方便，尤其對不方便維護長連線的場景。
2. 廢棄了原來的目錄結構，變成了純粹的 kv，使用者可以透過字首匹配模式模擬目錄。
3. 記憶體中不再儲存 value，同樣的記憶體可以支援儲存更多的 key。
4. watch 機制更穩定，基本上可以透過 watch 機制實現資料的完全同步。
5. 提供了批次操作以及事務機制，使用者可以透過批次事務請求來實現 Etcd v2 的 CAS 機制（批次事務支援 if 條件判斷）。

## Etcd，Zookeeper，Consul 比較

* Etcd 和 Zookeeper 提供的能力非常相似，都是通用的一致性元資訊儲存，都提供 watch 機制用於變更通知和分發，也都被分散式系統用來作為共享資訊儲存，在軟體生態中所處的位置也幾乎是一樣的，可以互相替代的。二者除了實現細節，語言，一致性協議上的區別，最大的區別在周邊生態圈。Zookeeper 是 apache 下的，用 java 寫的，提供 rpc 介面，最早從 hadoop 專案中孵化出來，在分散式系統中得到廣泛使用（hadoop, solr, kafka, mesos 等）。Etcd 是 coreos 公司旗下的開源產品，比較新，以其簡單好用的 rest 介面以及活躍的社群俘獲了一批使用者，在新的一些叢集中得到使用（比如 kubernetes）。雖然 v3 為了效能也改成二進位制 rpc 介面了，但其易用性上比 Zookeeper 還是好一些。
* 而 Consul 的目標則更為具體一些，Etcd 和 Zookeeper 提供的是分散式一致性儲存能力，具體的業務場景需要使用者自己實現，比如服務發現，比如設定變更。而 Consul 則以服務發現和設定變更為主要目標，同時附帶了 kv 儲存。

## Etcd 的周邊工具

1. **Confd**

   在分散式系統中，理想情況下是應用程式直接和 Etcd 這樣的服務發現 / 設定中心互動，透過監聽 Etcd 進行服務發現以及設定變更。但我們還有許多歷史遺留的程式，服務發現以及設定大多都是透過變更設定檔案進行的。Etcd 自己的定位是通用的 kv 儲存，所以並沒有像 Consul 那樣提供實現設定變更的機制和工具，而 Confd 就是用來實現這個目標的工具。

   Confd 透過 watch 機制監聽 Etcd 的變更，然後將資料同步到自己的一個本地儲存。使用者可以透過設定定義自己關注哪些 key 的變更，同時提供一個設定檔案模板。Confd 一旦發現資料變更就使用最新資料渲染模板生成設定檔案，如果新舊設定檔案有變化，則進行替換，同時觸發使用者提供的 reload 指令碼，讓應用程式重新載入設定。

   Confd 相當於實現了部分 Consul 的 agent 以及 consul-template 的功能，作者是 kubernetes 的 Kelsey Hightower，但大神貌似很忙，沒太多時間關注這個專案了，很久沒有釋出版本，我們著急用，所以 fork 了一份自己更新維護，主要增加了一些新的模板函式以及對 metad 後端的支援。[confd](https://github.com/yunify/confd)

2. **Metad**

   服務註冊的實現模式一般分為兩種，一種是排程系統代為註冊，一種是應用程式自己註冊。排程系統代為註冊的情況下，應用程式啟動後需要有一種機制讓應用程式知道『我是誰』，然後發現自己所在的叢集以及自己的設定。Metad 提供這樣一種機制，客戶端請求 Metad 的一個固定的介面 /self，由 Metad 告知應用程式其所屬的元資訊，簡化了客戶端的服務發現和設定變更邏輯。

   Metad 透過儲存一個 ip 到元資訊路徑的對映關係來做到這一點，當前後端支援 Etcd v3，提供簡單好用的 http rest 介面。 它會把 Etcd 的資料透過 watch 機制同步到本地記憶體中，相當於 Etcd 的一個代理。所以也可以把它當做 Etcd 的代理來使用，適用於不方便使用 Etcd v3 的 rpc 介面或者想降低 Etcd 壓力的場景。 [metad](https://github.com/yunify/metad)

## Etcd 使用注意事項

1. Etcd cluster 初始化的問題

   如果叢集第一次初始化啟動的時候，有一臺節點未啟動，透過 v3 的介面存取的時候，會報告 Error: Etcdserver: not capable 錯誤。這是為相容性考慮，叢集啟動時預設的 API 版本是 2.3，只有當叢集中的所有節點都加入了，確認所有節點都支援 v3 介面時，才提升叢集版本到 v3。這個只有第一次初始化叢集的時候會遇到，如果叢集已經初始化完畢，再掛掉節點，或者叢集關閉重啟（關閉重啟的時候會從持久化資料中載入叢集 API 版本），都不會有影響。

2. Etcd 讀請求的機制

   v2 quorum=true 的時候，讀取是透過 raft 進行的，透過 cli 請求，該引數預設為 true。

   v3 --consistency=“l” 的時候（預設）透過 raft 讀取，否則讀取本地資料。sdk 程式碼裡則是透過是否開啟：WithSerializable option 來控制。

   一致性讀取的情況下，每次讀取也需要走一次 raft 協議，能保證一致性，但效能有損失，如果出現網路分割槽，叢集的少數節點是不能提供一致性讀取的。但如果不設定該引數，則是直接從本地的 store 裡讀取，這樣就損失了一致性。使用的時候需要注意根據應用場景設定這個引數，在一致性和可用性之間進行取捨。

3. Etcd 的 compact 機制

   Etcd 預設不會自動 compact，需要設定啟動引數，或者透過命令進行 compact，如果變更頻繁建議設定，否則會導致空間和記憶體的浪費以及錯誤。Etcd v3 的預設的 backend quota 2GB，如果不 compact，boltdb 檔案大小超過這個限制後，就會報錯：”Error: etcdserver: mvcc: database space exceeded”，導致資料無法寫入。

## etcd 的問題

```text
当前 Etcd 的 raft 实现保证了多个节点数据之间的同步，但明显的一个问题就是扩充节点不能解决容量问题。要想解决容量问题，只能进行分片，但分片后如何使用 raft 同步数据？只能实现一个 multiple group raft，每个分片的多个副本组成一个虚拟的 raft group，通过 raft 实现数据同步。当前实现了 multiple group raft 的有 TiKV 和 Cockroachdb，但尚未一个独立通用的。理论上来说，如果有了这套 multiple group raft，后面挂个持久化的 kv 就是一个分布式 kv 存储，挂个内存 kv 就是分布式缓存，挂个 lucene 就是分布式搜索引擎。当然这只是理论上，要真实现复杂度还是不小。
```

注： 部分轉自 [jolestar](http://jolestar.com/etcd-architecture/) 和[infoq](http://www.infoq.com/cn/articles/etcd-interpretation-application-scenario-implement-principle).

## 參考文件

* [Etcd website](https://coreos.com/etcd/)
* [Etcd github](https://github.com/coreos/etcd/)
* [Projects using etcd](https://etcd.io/docs/v3.5/integrations/#projects-using-etcd)
* [http://jolestar.com/etcd-architecture/](http://jolestar.com/etcd-architecture/)
* [etcd 從應用場景到實現原理的全方位解讀](http://www.infoq.com/cn/articles/etcd-interpretation-application-scenario-implement-principle)
