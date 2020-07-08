/**
*该文件内容是mysql客户端对应的后台表结构与存储过程， 下面的示例是在名字未`wordpress`的数据库
*只要保证表与存储过程建立在同一个数据库，对具体数据库名字不限制。
*对表名/字段名，以及存储过程，由于代码中需要引用，所以不能变动，除非进行了必要的排查/替换工作
*/


/**
表结构
*/
CREATE DATABASE /*!32312 IF NOT EXISTS*/`wordpress` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `wordpress`;

/*Table structure for table `auction_items_tbl` */

DROP TABLE IF EXISTS `auction_items_tbl`;

CREATE TABLE `auction_items_tbl` (
  `id` varchar(32) NOT NULL COMMENT 'md5(url)',
  `title` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `url` varchar(1024) NOT NULL COMMENT '标的详单地址',
  `atten` text,
  `rec` text,
  `notice` text,
  `intro` text,
  `attachs` text,
  `video` text,
  `images` text,
  `preferred` text,
  `state` varchar(256) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `datetime` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  FULLTEXT KEY `notice` (`notice`),
  FULLTEXT KEY `title` (`title`),
  FULLTEXT KEY `state` (`state`),
  FULLTEXT KEY `atten` (`atten`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

/*Table structure for table `auction_items_url_tbl` */

DROP TABLE IF EXISTS `auction_items_url_tbl`;

CREATE TABLE `auction_items_url_tbl` (
  `datetime` datetime NOT NULL COMMENT '首次收集到的时间',
  `url` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '标的详详情页url',
  `state` smallint NOT NULL DEFAULT '0' COMMENT '0:未抓取详情页，-1:已被爬虫收集待抓取  1：已经抓取',
  `id` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT 'md5(url)',
  `spider` varchar(32) NOT NULL COMMENT 'spider name',
  PRIMARY KEY (`id`),
  KEY `DATETIME` (`datetime`),
  KEY `url` (`url`),
  KEY `spidername` (`spider`),
  KEY `state` (`state`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


/**
mysql client 实现的后台表结构与存储过程
*/

DROP PROCEDURE IF EXISTS `insert_auction_item`;

DELIMITER $$

-- 入库抓取详单，同时更新想到url状态为1状态，代表已被抓取过
CREATE    PROCEDURE `insert_auction_item`(IN _id VARCHAR(32), IN _title VARCHAR(1024), IN _url VARCHAR(1024), 
                                                IN _atten TEXT, IN _rec TEXT, IN _notice TEXT,IN _intro TEXT,IN _attachs TEXT,
                                                IN _video TEXT,IN _images TEXT,IN _preferred TEXT,IN _state VARCHAR(100), IN _spider VARCHAR(32), OUT _success TINYINT)
    /*LANGUAGE SQL
    | [NOT] DETERMINISTIC
    | { CONTAINS SQL | NO SQL | READS SQL DATA | MODIFIES SQL DATA }
    | SQL SECURITY { DEFINER | INVOKER }
    | COMMENT 'string'*/
	BEGIN
	    -- #定义一个变量来保存该记录是否存在
	    DECLARE itemnum INT DEFAULT 0;
	    DECLARE urlnum INT DEFAULT 0;
	    
	    DECLARE t_error INT DEFAULT 0;
	    DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET t_error=1 ; 
	    START TRANSACTION; 
	    -- # 
	    SELECT COUNT(*) INTO itemnum FROM `auction_items_tbl`  WHERE `id` = _id;
	    SELECT COUNT(*) INTO urlnum FROM `auction_items_url_tbl`  WHERE `id` = _id;
	    -- #	    
	    IF itemnum >0 THEN
		UPDATE  `auction_items_tbl` AS tbl SET 
		  `title` = _title,  `url` = _url,  `atten` = _atten,  `rec` = _rec,  `notice` = _notice,  `intro` = _intro,
		  `attachs` = _attachs,  `video` = _video,  `images` = _images,  `preferred` = _preferred,  `state` = _state,  `datetime` = NOW()
		  WHERE `id` = _id;		
	    ELSE
		INSERT INTO `auction_items_tbl` (
		  `id`, `title`,`url`,`atten`, `rec`,`notice`, `intro`,  `attachs`,`video`,`images`,`preferred`,`state`, `datetime` )
		  VALUES (  _id, _title,_url,_atten,_rec,_notice,_intro,  _attachs,_video,_images,_preferred,_state,NOW() );
	    END IF;	    

        -- # 补齐地址列表信息	    
        IF urlnum >0 THEN
	        UPDATE `auction_items_url_tbl` AS tbl SET tbl.`state` = 1 WHERE `id` = _id;
	    ELSE
	        INSERT INTO `auction_items_url_tbl` ( `id`,`spider`, `url`, `datetime`,`state` )  VALUES (_id, _spider, _url, NOW(), 1);
	    END IF;	
	    
	    -- 默认认为失败
	    SET  _success = 0;
	    IF t_error = 1 THEN
	       ROLLBACK;
	    ELSE
	       COMMIT;
	       SET _success = 1;
	    END IF;     

	END$$

DELIMITER ;


DROP PROCEDURE IF EXISTS `getauctionitemurls`;

DELIMITER $$

-- 爬取预取0状态详单url，同时更新状态未-1状态，代表爬虫预取
-- 返回结果是"id url"列表
CREATE
    /*[DEFINER = { user | CURRENT_USER }]*/
    PROCEDURE `wordpress`.`getauctionitemurls`(IN _max TINYINT, IN _spider VARCHAR(32), OUT num INT )
    /*LANGUAGE SQL
    | [NOT] DETERMINISTIC
    | { CONTAINS SQL | NO SQL | READS SQL DATA | MODIFIES SQL DATA }
    | SQL SECURITY { DEFINER | INVOKER }
    | COMMENT 'string'*/
    BEGIN          
        DECLARE size INT DEFAULT 0;
        # 使用临时表
        CREATE TEMPORARY TABLE  IF NOT EXISTS temp_result (
           `url` VARCHAR(1024),
           `id` VARCHAR(32)  ,
           PRIMARY KEY (`id`)
        );

        TRUNCATE TABLE temp_result;
        #fetch
        INSERT INTO temp_result (id, url) 
            SELECT  `id`,`url` FROM `auction_items_url_tbl` 
                   WHERE `state` = 0 AND `spider`=_spider ORDER BY `datetime` DESC LIMIT _max OFFSET 0;
        #
        UPDATE `auction_items_url_tbl` AS tb SET tb.`state` = -1  
            WHERE EXISTS(SELECT * FROM temp_result WHERE `id` = tb.`id`) ;
        
        SELECT COUNT(*) INTO size FROM temp_result; 
        SET num = size;
        SELECT `id`, `url` FROM temp_result;

    END$$

DELIMITER ;




-- DROP PROCEDURE IF EXISTS `getauctionitemurls`;

-- DELIMITER $$

-- -- 爬取预取0状态详单url，同时更新状态未-1状态，代表爬虫预取
-- -- 返回结果是"id url, id url,....,"结构的字符串
-- CREATE
--     /*[DEFINER = { user | CURRENT_USER }]*/
--     PROCEDURE `getauctionitemurls`(IN _max TINYINT, IN _spider VARCHAR(32) ,OUT _urls TEXT)
--     /*LANGUAGE SQL
--     | [NOT] DETERMINISTIC
--     | { CONTAINS SQL | NO SQL | READS SQL DATA | MODIFIES SQL DATA }
--     | SQL SECURITY { DEFINER | INVOKER }
--     | COMMENT 'string'*/
-- 	BEGIN   
-- 	DECLARE val VARCHAR(2048) DEFAULT "";
-- 	    DECLARE temp_str TEXT DEFAULT ""; 
--         DECLARE dyn_sql VARCHAR(500);
--         DECLARE id_ VARCHAR(32);
--         DECLARE url_ VARCHAR(1024);
        
--         DECLARE num INT DEFAULT 0;
-- 	    -- 声明游标
--         DECLARE urls_list CURSOR FOR  SELECT `id`,`url` FROM `auction_items_url_tbl` WHERE `state` = 0 AND `spider`=_spider ORDER BY `datetime` DESC LIMIT _max OFFSET 0;
--         -- 声明当游标遍历完全部记录后将标志变量置成某个值
--         DECLARE CONTINUE HANDLER FOR NOT FOUND SET num=1;
        
--         -- 打开游标
--         OPEN urls_list;
-- 		-- 将游标中的值赋值给变量，要注意sql结果列的顺序
-- 		FETCH urls_list INTO id_, url_; 
-- 		-- while循环
-- 		WHILE num <> 1 DO
-- 		    START TRANSACTION;
-- 		    -- '-1'代表临时被拿走了
-- 		    UPDATE `auction_items_url_tbl` AS tbl SET tbl.`state` = -1  WHERE tbl.`id` = id_ ;
			
-- 		    SET val = CONCAT( id_, ":", url_ );
-- 			IF temp_str = "" THEN
-- 			   SET temp_str = val;
-- 			ELSE
-- 			    SET temp_str = CONCAT(val , "," ,temp_str);
-- 			END IF;
			
-- 			COMMIT;
-- 			FETCH urls_list INTO id_, url_; 
-- 		END WHILE;
-- 	    -- 关闭游标
--         CLOSE urls_list;
            
--         SET _urls = temp_str;

-- 	END$$
-- DELIMITER ;


