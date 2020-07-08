#!/bin/bash

custpython="/home/atmel/spider/bin/python3"

script="/home/atmel/spider-demo/seleni/cli/runspider.py"

########################################

SECONDS=0
# # 人民法院诉讼资产网
${custpython} ${script}  --spider rmfysszc -c list  -s "TWISTED_REACTOR" "twisted.internet.pollreactor.PollReactor" "https://www1.rmfysszc.gov.cn/projects.shtml"
duration=$SECONDS
echo "rmfysszc grab urls elapsed: $(($duration / 60)) minutes and $(($duration % 60)) seconds"

sleep  3s

SECONDS=0
# #  京东拍卖-司法拍卖网：
${custpython} ${script}  --spider jdsifa -c list  -s "TWISTED_REACTOR" "twisted.internet.pollreactor.PollReactor" "https://auction.jd.com/sifa_list.html"
duration=$SECONDS
echo "jdsifa   grab urls elapsed: $(($duration / 60)) minutes and $(($duration % 60)) seconds"

sleep  3s

SECONDS=0
# #  公拍网：
${custpython} ${script}  --spider gpai -c list  -s "TWISTED_REACTOR" "twisted.internet.pollreactor.PollReactor" "http://s.gpai.net/sf/search.do?action=court"
duration=$SECONDS
echo "gpai     grab urls elapsed: $(($duration / 60)) minutes and $(($duration % 60)) seconds"

sleep  3s

SECONDS=0
# #拍卖行业协会网 司法拍卖
${custpython} ${script}  --spider sfcaa123 -c list  -s "TWISTED_REACTOR" "twisted.internet.pollreactor.PollReactor" "https://sf.caa123.org.cn/pages/lots.html?lotMode=2"
duration=$SECONDS
echo "sfcaa123 grab urls elapsed: $(($duration / 60)) minutes and $(($duration % 60)) seconds"

SECONDS=0
${custpython} ${script}  --spider  tbsifa -c list  -s "TWISTED_REACTOR" "twisted.internet.pollreactor.PollReactor" "https://sf.taobao.com/item_list.htm?spm=a213w.7398504.pagination.2.6e357ddatzTQlU&auction_source=0&st_param=-1&auction_start_seg=-1&page=1"
duration=$SECONDS
echo "tbsifa   grab urls elapsed: $(($duration / 60)) minutes and $(($duration % 60)) seconds"



#############################################

#爬取结果，由于这个没有给出urls，这 意味着需要从数据库中获取待爬取标的url
SECONDS=0
${custpython} ${script}    --spider tbsifa -c result
duration=$SECONDS
echo "tbsifa   grab itme elapsed: $(($duration / 60)) minutes and $(($duration % 60)) seconds"

sleep  3s

SECONDS=0
${custpython} ${script}    --spider rmfysszc -c result
duration=$SECONDS
echo "rmfysszc grab item elapsed: $(($duration / 60)) minutes and $(($duration % 60)) seconds"

sleep  3s

SECONDS=0
${custpython} ${script}    --spider jdsifa -c result  -s "TWISTED_REACTOR" "twisted.internet.pollreactor.PollReactor"
duration=$SECONDS
echo "jdsifa   grab item elapsed: $(($duration / 60)) minutes and $(($duration % 60)) seconds"

SECONDS=0
${custpython} ${script}    --spider gpai -c result
duration=$SECONDS
echo "gpai     grab itme elapsed: $(($duration / 60)) minutes and $(($duration % 60)) seconds"

sleep  3s

SECONDS=0
${custpython} ${script}    --spider sfcaa123 -c result -s "TWISTED_REACTOR" "twisted.internet.pollreactor.PollReactor"
duration=$SECONDS
echo "sfcaa123 grab itme elapsed: $(($duration / 60)) minutes and $(($duration % 60)) seconds"

