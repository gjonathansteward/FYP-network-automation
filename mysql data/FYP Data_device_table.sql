-- MySQL dump 10.13  Distrib 5.7.21, for Linux (x86_64)
--
-- Host: localhost    Database: FYP Data
-- ------------------------------------------------------
-- Server version	5.7.21-0ubuntu0.16.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `device_table`
--

DROP TABLE IF EXISTS `device_table`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `device_table` (
  `device_id` int(11) NOT NULL AUTO_INCREMENT,
  `ip` varchar(45) DEFAULT NULL,
  `vendor` varchar(45) DEFAULT NULL,
  `community` varchar(45) DEFAULT NULL,
  `username` varchar(45) DEFAULT NULL,
  `loginpassword` varchar(45) DEFAULT NULL,
  `enpassword` varchar(45) DEFAULT NULL,
  `config_lock` int(11) DEFAULT NULL,
  `config_lock_reason` varchar(45) DEFAULT NULL,
  `asn` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`device_id`),
  UNIQUE KEY `device_ip_UNIQUE` (`ip`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=big5;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `device_table`
--

LOCK TABLES `device_table` WRITE;
/*!40000 ALTER TABLE `device_table` DISABLE KEYS */;
INSERT INTO `device_table` VALUES (1,'10.10.10.1','cisco','public','admin','cisco','cisco',0,'','1'),(2,'20.20.20.1','cisco','public','admin','cisco','cisco',0,'','2'),(3,'192.168.1.1','cisco','public','admin','cisco','cisco',0,NULL,NULL),(4,'30.30.30.1','juniper','public','admin','cisco12345','',0,'','1'),(6,'40.40.40.1','juniper','public','admin','cisco12345',NULL,0,'','2'),(7,'25.4.2.25','juniper','public','fake','fake','fake',0,NULL,NULL);
/*!40000 ALTER TABLE `device_table` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2018-05-07 15:02:53
