CREATE DATABASE house_spider DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;

#ip池信息
create table ip_pool
(
id bigint primary key not null auto_increment
,ip varchar(200) comment 'ip'
,port varchar(50) comment 'port'
,location varchar(200) comment '位置'
,is_active int comment '是否可用 1可用 0不可用'
,dt varchar(20)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

#安居客二手房数据
create table ajk_sh
(
id bigint primary key not null auto_increment
,addr varchar(200) comment '小区名字'
,district varchar(50) comment '区县'
,unit_price decimal(14,2) comment '平米单价'
,dt varchar(50)   comment '录入日期'
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

#安居客租售比信息
create table ajk_rent_sale_ratio
(
id bigint primary key not null auto_increment
,addr varchar(200) comment '小区名字'
,district varchar(50) comment '区县'
,avg_sale decimal(12,4) comment '售价-均价'
,avg_rent decimal(12,4) comment '组价-均价'
,rent_sale_ratio decimal(12,4) comment '租售比'
,dt varchar(50)   comment '录入日期'
)ENGINE=InnoDB DEFAULT CHARSET=utf8;