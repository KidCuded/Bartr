-- Database backup created on 2025-06-19 09:50:12.637858
-- Backup file: backup_20250619_095012.sql

SET FOREIGN_KEY_CHECKS = 0;

-- Table: category
DROP TABLE IF EXISTS `category`;
CREATE TABLE `category` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `order` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `category` (`id`, `name`, `description`, `order`) VALUES
(1, 'Electronics & Gadgets', 'Phones, laptops, tablets, and other electronic devices', 0),
(2, 'Fashion', 'Clothing, accessories, and footwear for men and women', 1),
(3, 'Watches & Accessories', 'Watches, jewelry, and fashion accessories', 2),
(4, 'Beauty & Personal Care', 'Cosmetics, skincare, and personal care items', 3),
(5, 'Gaming & Entertainment', 'Gaming consoles, games, and entertainment equipment', 4),
(6, 'Photography & Audio', 'Cameras, audio equipment, and related accessories', 5),
(7, 'Home & Living', 'Furniture, appliances, and home decor', 6),
(8, 'Sports & Outdoors', 'Sports equipment, outdoor gear, and fitness items', 8),
(9, 'Kids & Baby', 'Baby gear, toys, and children''s items', 10),
(10, 'Books & Hobbies', 'Books, collectibles, and hobby items', 7),
(11, 'Tickets & Vouchers', 'Event tickets, gift cards, and vouchers', 11),
(12, 'Automotive', 'Auto parts, accessories, and car care items', 12),
(14, 'Toys & Games', '', 9),
(15, 'Others', 'Items that don''t fit in other categories', 13);

-- Table: favorite
DROP TABLE IF EXISTS `favorite`;
CREATE TABLE `favorite` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `item_id` int(11) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `item_id` (`item_id`),
  CONSTRAINT `favorite_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
  CONSTRAINT `favorite_ibfk_2` FOREIGN KEY (`item_id`) REFERENCES `item` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `favorite` (`id`, `user_id`, `item_id`, `created_at`) VALUES
(1, 2, 18, '2025-06-15 09:06:55'),
(2, 1, 16, '2025-06-15 10:45:07'),
(3, 1, 15, '2025-06-15 10:45:10'),
(4, 4, 18, '2025-06-17 12:14:45');

-- Table: flag
DROP TABLE IF EXISTS `flag`;
CREATE TABLE `flag` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `item_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `violation_type` varchar(50) NOT NULL,
  `reason` text DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `item_id` (`item_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `flag_ibfk_1` FOREIGN KEY (`item_id`) REFERENCES `item` (`id`),
  CONSTRAINT `flag_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `flag` (`id`, `item_id`, `user_id`, `violation_type`, `reason`, `created_at`, `status`) VALUES
(1, 11, 4, 'spam', 'This item appeared to be a spam', '2025-06-18 03:59:15', 'pending');

-- Table: item
DROP TABLE IF EXISTS `item`;
CREATE TABLE `item` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `condition` varchar(50) DEFAULT NULL,
  `category_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `estimated_value` float DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `is_flagged` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `category_id` (`category_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `item_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `category` (`id`),
  CONSTRAINT `item_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `item` (`id`, `name`, `description`, `condition`, `category_id`, `user_id`, `estimated_value`, `created_at`, `is_active`, `is_flagged`) VALUES
(1, 'Apple MacBook Air (2022) ', '', 'like_new', 1, 2, 2500.0, '2025-06-15 06:51:23', 1, 0),
(2, 'Onitsuka Tiger Mexico 66 SD', '', 'brand_new', 2, 2, 600.0, '2025-06-15 06:51:58', 1, 0),
(3, 'Logitech G923 w shifter', '', 'lightly_used', 5, 2, 600.0, '2025-06-15 06:53:10', 1, 0),
(4, 'MONTIGO Stone Ace Bottle Mega (950ml)', '', 'brand_new', 7, 2, 80.0, '2025-06-15 06:53:30', 1, 0),
(5, 'To Kill a Mockingbird', '', 'lightly_used', 10, 2, 30.0, '2025-06-15 06:54:01', 1, 0),
(6, 'Adidas Samba OG', '', 'lightly_used', 2, 2, 400.0, '2025-06-15 06:54:47', 1, 0),
(7, 'iPhone 12', 'White, 512GB', 'like_new', 1, 1, 1200.0, '2025-06-15 06:56:18', 1, 0),
(8, 'Fuji Film Instax mini 9', '', 'lightly_used', 6, 1, 300.0, '2025-06-15 06:58:32', 1, 0),
(9, 'Apple Watch Ultra 1 49MM GPS + Cellular', '', 'like_new', 3, 2, 1480.0, '2025-06-15 07:01:53', 1, 0),
(10, 'DJI OSMO POCKET3', '', 'like_new', 6, 2, 1100.0, '2025-06-15 07:04:03', 1, 0),
(11, 'Apple AirPods Max', '', 'like_new', 6, 1, 1600.0, '2025-06-15 07:05:27', 1, 1),
(12, 'CRBN X Series Power 3X Pickleball Paddles', 'Carbon fibre T700 1 PCS, USAPA Approved Composite Pickleball', 'brand_new', 8, 2, 200.0, '2025-06-15 07:07:09', 1, 0),
(13, 'BLACKDOG Cinema Tent ver 2', '', 'lightly_used', 8, 1, 1000.0, '2025-06-15 07:09:23', 1, 0),
(14, 'TV console / cabinet', '', 'well_used', 7, 4, 180.0, '2025-06-15 07:13:13', 1, 0),
(15, 'San-x rilakkuma korilakkuma limited edition', '', 'like_new', 14, 4, 600.0, '2025-06-15 07:16:21', 1, 0),
(16, 'Ibanez RG Superstrat RG370AHMZ', '', 'like_new', 10, 4, 1900.0, '2025-06-15 07:19:04', 1, 0),
(17, 'Stainless Steel Litter Box', '', 'like_new', 7, 4, 60.0, '2025-06-15 07:20:31', 1, 0),
(18, 'LG 55” 4K UHF smart tv 55UQ8050PSB', '', 'like_new', 1, 4, 1200.0, '2025-06-15 07:22:03', 1, 0);

-- Table: item_photo
DROP TABLE IF EXISTS `item_photo`;
CREATE TABLE `item_photo` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `item_id` int(11) NOT NULL,
  `photo_path` varchar(255) NOT NULL,
  `order` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `item_id` (`item_id`),
  CONSTRAINT `item_photo_ibfk_1` FOREIGN KEY (`item_id`) REFERENCES `item` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=52 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `item_photo` (`id`, `item_id`, `photo_path`, `order`, `created_at`) VALUES
(1, 1, 'macbook_air_m1_chip_13_inch_1749707571_40ef7e03_progressive.jpg', 0, '2025-06-15 06:51:24'),
(2, 1, 'macbook_air_m1_chip_13_inch_1749707571_774eed3a_progressive.jpg', 1, '2025-06-15 06:51:24'),
(3, 1, 'macbook_air_m1_chip_13_inch_1749707571_ca1055b7_progressive.jpg', 2, '2025-06-15 06:51:24'),
(4, 1, 'macbook_air_m1_chip_13_inch_1749707571_2f6b12d2_progressive.jpg', 3, '2025-06-15 06:51:24'),
(5, 2, 'onitsuka_tiger_mexico_66_sd_1747923164_226a8e5f_progressive.jpg', 0, '2025-06-15 06:51:58'),
(6, 2, 'onitsuka_tiger_mexico_66_sd_1747923164_d342a5cc_progressive.jpg', 1, '2025-06-15 06:51:58'),
(7, 2, 'onitsuka_tiger_mexico_66_sd_1747923164_fc2842e5_progressive.jpg', 2, '2025-06-15 06:51:58'),
(8, 3, 'logitech_g923_w_shifter_1749116576_8e73827d_progressive.jpg', 0, '2025-06-15 06:53:10'),
(9, 3, 'logitech_g923_w_shifter_1749116516_4b33c0b7_progressive.jpg', 1, '2025-06-15 06:53:10'),
(10, 3, 'logitech_g923_w_shifter_1749116516_4099ec7f_progressive.jpg', 2, '2025-06-15 06:53:10'),
(11, 3, 'logitech_g923_w_shifter_1749116932_449505e1_progressive.jpg', 3, '2025-06-15 06:53:10'),
(12, 4, 'montigo_stone_ace_bottle_mega__1749045720_0dcbfb07_progressive.jpg', 0, '2025-06-15 06:53:30'),
(13, 4, 'montigo_stone_ace_bottle_mega__1749728594_557cc5f9_progressive.jpg', 1, '2025-06-15 06:53:30'),
(14, 5, 'to-kill-a-mockingbird-harper-lee-bookbed.png', 0, '2025-06-15 06:54:01'),
(15, 6, 'adidas_samba_og_1744464285_7a52c5f7_progressive.jpg', 0, '2025-06-15 06:54:47'),
(16, 6, 'adidas_samba_og_1744464285_e7feef07_progressive.jpg', 1, '2025-06-15 06:54:47'),
(17, 6, 'adidas_samba_og_1744464285_2824f1d2_progressive.jpg', 2, '2025-06-15 06:54:47'),
(18, 6, 'adidas_samba_og_1744464285_7e597438_progressive.jpg', 3, '2025-06-15 06:54:47'),
(19, 7, 'iphone_12_256gb_white_1748588765_9525b58b_progressive.jpeg', 0, '2025-06-15 06:56:18'),
(20, 7, 'iphone_12_256gb_white_1748588765_de9c616b_progressive.jpeg', 1, '2025-06-15 06:56:18'),
(21, 7, 'iphone_12_256gb_white_1748588765_729cf6e3_progressive.jpeg', 2, '2025-06-15 06:56:18'),
(22, 8, 'kamera_fuji_film_instax_mini_9_1747726518_1d563530_progressive.jpg', 0, '2025-06-15 06:58:32'),
(23, 8, 'kamera_fuji_film_instax_mini_9_1747726518_a990e4fe_progressive.jpg', 1, '2025-06-15 06:58:32'),
(24, 8, 'kamera_fuji_film_instax_mini_9_1747726518_17ba189a_progressive.jpg', 2, '2025-06-15 06:58:32'),
(25, 8, 'kamera_fuji_film_instax_mini_9_1747726518_7ab8b7e2_progressive.jpg', 3, '2025-06-15 06:58:32'),
(26, 9, 'apple_watch_ultra_1_49mm_gps___1749860594_7bd8a741_progressive.jpg', 0, '2025-06-15 07:01:53'),
(27, 9, 'apple_watch_ultra_1_49mm_gps___1749860594_a3ae6341_progressive.jpg', 1, '2025-06-15 07:01:53'),
(28, 9, 'apple_watch_ultra_1_49mm_gps___1749860594_58d1375e_progressive.jpg', 2, '2025-06-15 07:01:53'),
(29, 9, 'apple_watch_ultra_1_49mm_gps___1749860594_fa20d711_progressive.jpg', 3, '2025-06-15 07:01:53'),
(30, 9, 'apple_watch_ultra_1_49mm_gps___1749860594_9892dc56_progressive.jpg', 4, '2025-06-15 07:01:53'),
(31, 10, 'dji_osmo_pocket3_1748935270_09bd3f69_progressive.jpeg', 0, '2025-06-15 07:04:03'),
(32, 10, 'dji_osmo_pocket3_1748935270_9715c998_progressive.jpeg', 1, '2025-06-15 07:04:03'),
(33, 10, 'dji_osmo_pocket3_1748935270_12a206ca_progressive.jpeg', 2, '2025-06-15 07:04:03'),
(34, 10, 'dji_osmo_pocket3_1748935270_18fbd5ce_progressive.jpeg', 3, '2025-06-15 07:04:03'),
(35, 11, 'apple_airpods_max_1738822567_488a517e_progressive.jpg', 0, '2025-06-15 07:05:27'),
(36, 11, 'apple_airpods_max_1738822567_37d13153_progressive.jpg', 1, '2025-06-15 07:05:27'),
(37, 11, 'apple_airpods_max_1738822567_e8c84491_progressive.jpg', 2, '2025-06-15 07:05:27'),
(38, 11, 'apple_airpods_max_1738822567_1cd66321_progressive.jpg', 3, '2025-06-15 07:05:27'),
(39, 12, 'crbn_x_series_power_3x_pickleb_1732709371_b8b172c8_progressive.jpg', 0, '2025-06-15 07:07:09'),
(40, 13, 'blackdog_cinema_tent_upgraded__1748687396_f75f40b4_progressive.jpg', 0, '2025-06-15 07:09:23'),
(41, 13, 'blackdog_cinema_tent_upgraded__1748687396_ba687402_progressive.jpg', 1, '2025-06-15 07:09:23'),
(42, 13, 'blackdog_cinema_tent_upgraded__1748687396_c94ee074_progressive.jpg', 2, '2025-06-15 07:09:23'),
(43, 14, 'tv_console__cabinet_1743434331_e744ce8a_progressive.jpg', 0, '2025-06-15 07:13:13'),
(44, 15, 'sanx_rilakkuma_korilakkuma_lim_1747057149_16ef9b4e_progressive.jpg', 0, '2025-06-15 07:16:21'),
(45, 15, 'sanx_rilakkuma_korilakkuma_lim_1747057149_241634a4_progressive.jpg', 1, '2025-06-15 07:16:21'),
(46, 16, 'ibanez_rg_superstrat_1745213130_3f3c1849_progressive.jpg', 0, '2025-06-15 07:19:04'),
(47, 16, 'ibanez_rg_superstrat_1745213130_00f8881d_progressive.jpg', 1, '2025-06-15 07:19:04'),
(48, 16, 'ibanez_rg_superstrat_1745213130_0e746a2a_progressive.jpg', 2, '2025-06-15 07:19:04'),
(49, 17, 'stainless_steel_litter_box_1749970365_4fb5bc8a_progressive.jpg', 0, '2025-06-15 07:20:31'),
(50, 17, 'stainless_steel_litter_box_1749970365_6b4a21c8_progressive.jpg', 1, '2025-06-15 07:20:31'),
(51, 18, 'lg_55uq8050psb_1749898005_6f712b5a_progressive.jpg', 0, '2025-06-15 07:22:03');

-- Table: message
DROP TABLE IF EXISTS `message`;
CREATE TABLE `message` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sender_id` int(11) NOT NULL,
  `receiver_id` int(11) NOT NULL,
  `content` text DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `is_read` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `sender_id` (`sender_id`),
  KEY `receiver_id` (`receiver_id`),
  CONSTRAINT `message_ibfk_1` FOREIGN KEY (`sender_id`) REFERENCES `user` (`id`),
  CONSTRAINT `message_ibfk_2` FOREIGN KEY (`receiver_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `message` (`id`, `sender_id`, `receiver_id`, `content`, `created_at`, `is_read`) VALUES
(1, 2, 1, '🔄 Trade Proposal Requesting: Apple AirPods Max
Offering: Apple Watch Ultra 1 49MM GPS + Cellular', '2025-06-15 07:31:36', 1),
(2, 2, 4, '🔄 Trade Proposal Requesting: LG 55” 4K UHF smart tv 55UQ8050PSB
Offering: DJI OSMO POCKET3', '2025-06-15 07:32:45', 0),
(3, 2, 4, '🔄 Trade Proposal Requesting: San-x rilakkuma korilakkuma limited edition
Offering: Logitech G923 w shifter', '2025-06-17 09:06:05', 0),
(4, 2, 4, 'hi i want to trade with this can?? or cannot?? better be can, how do i contact you??', '2025-06-17 09:06:05', 0),
(5, 4, 1, '🔄 Trade Proposal Requesting: iPhone 12
Offering: TV console / cabinet, San-x rilakkuma korilakkuma limited edition, Stainless Steel Litter Box', '2025-06-18 17:46:36', 0);

-- Table: message_image
DROP TABLE IF EXISTS `message_image`;
CREATE TABLE `message_image` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `message_id` int(11) NOT NULL,
  `image_path` varchar(255) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `message_id` (`message_id`),
  CONSTRAINT `message_image_ibfk_1` FOREIGN KEY (`message_id`) REFERENCES `message` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: notification
DROP TABLE IF EXISTS `notification`;
CREATE TABLE `notification` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `type` varchar(50) NOT NULL,
  `content` text NOT NULL,
  `is_read` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `item_id` int(11) DEFAULT NULL,
  `trade_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `item_id` (`item_id`),
  KEY `trade_id` (`trade_id`),
  CONSTRAINT `notification_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
  CONSTRAINT `notification_ibfk_2` FOREIGN KEY (`item_id`) REFERENCES `item` (`id`),
  CONSTRAINT `notification_ibfk_3` FOREIGN KEY (`trade_id`) REFERENCES `trade` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `notification` (`id`, `user_id`, `type`, `content`, `is_read`, `created_at`, `item_id`, `trade_id`) VALUES
(1, 1, 'trade_proposal', 'Charles has sent you a trade proposal for Apple AirPods Max', 1, '2025-06-15 07:31:36', 11, 1),
(2, 4, 'trade_proposal', 'Charles has sent you a trade proposal for LG 55” 4K UHF smart tv 55UQ8050PSB', 1, '2025-06-15 07:32:45', 18, 2),
(3, 4, 'trade_proposal', 'Charles has sent you a trade proposal for San-x rilakkuma korilakkuma limited edition', 1, '2025-06-17 09:06:05', 15, 3),
(4, 4, 'trade_cancelled', 'A trade proposal for your item San-x rilakkuma korilakkuma limited edition has been cancelled.', 1, '2025-06-17 09:06:34', NULL, 3),
(5, 4, 'trade_cancelled', 'A trade proposal for your item San-x rilakkuma korilakkuma limited edition has been cancelled.', 1, '2025-06-17 09:14:53', NULL, 3),
(6, 4, 'trade_cancelled', 'A trade proposal for your item San-x rilakkuma korilakkuma limited edition has been cancelled.', 1, '2025-06-17 09:15:10', NULL, 3),
(7, 4, 'trade_cancelled', 'A trade proposal for your item San-x rilakkuma korilakkuma limited edition has been cancelled.', 1, '2025-06-17 09:15:27', NULL, 3),
(8, 4, 'trade_cancelled', 'A trade proposal for your item San-x rilakkuma korilakkuma limited edition has been cancelled.', 1, '2025-06-17 09:16:11', NULL, 3),
(9, 4, 'trade_cancelled', 'A trade proposal for your item LG 55” 4K UHF smart tv 55UQ8050PSB has been cancelled.', 1, '2025-06-17 09:16:27', NULL, 2),
(10, 1, 'trade_cancelled', 'A trade proposal for your item Apple AirPods Max has been cancelled.', 0, '2025-06-17 09:17:28', NULL, 1),
(11, 1, 'trade_cancelled', 'A trade proposal for your item Apple AirPods Max has been cancelled.', 0, '2025-06-17 09:18:10', NULL, 1),
(12, 4, 'trade_cancelled', 'A trade proposal for your item LG 55” 4K UHF smart tv 55UQ8050PSB has been cancelled.', 1, '2025-06-17 09:18:52', NULL, 2),
(13, 4, 'trade_cancelled', 'A trade proposal for your item San-x rilakkuma korilakkuma limited edition has been cancelled.', 1, '2025-06-17 09:18:57', NULL, 3),
(14, 4, 'trade_cancelled', 'A trade proposal for your item San-x rilakkuma korilakkuma limited edition has been cancelled.', 1, '2025-06-17 09:22:02', NULL, 3),
(15, 4, 'trade_completion_reminder', 'Charles has marked the trade for LG 55” 4K UHF smart tv 55UQ8050PSB as completed. Please confirm completion within 48 hours.', 1, '2025-06-17 09:22:40', NULL, 2),
(16, 2, 'trade_accepted', 'Your trade proposal for LG 55” 4K UHF smart tv 55UQ8050PSB has been accepted!', 0, '2025-06-17 09:23:34', NULL, 2),
(17, 2, 'trade_rejected', 'Your trade proposal for San-x rilakkuma korilakkuma limited edition has been rejected.', 0, '2025-06-17 09:23:40', NULL, 3),
(18, 2, 'trade_cancelled', 'Your trade proposal for LG 55” 4K UHF smart tv 55UQ8050PSB has been cancelled by the item owner.', 0, '2025-06-17 09:23:44', NULL, 2),
(19, 2, 'trade_accepted', 'Your trade proposal for LG 55” 4K UHF smart tv 55UQ8050PSB has been accepted!', 0, '2025-06-17 11:31:34', NULL, 2),
(20, 2, 'trade_rejected', 'Your trade proposal for San-x rilakkuma korilakkuma limited edition has been rejected.', 0, '2025-06-17 11:32:48', NULL, 3),
(21, 1, 'flag', 'Your item ''Apple AirPods Max'' has been reported for: Spam', 0, '2025-06-18 03:59:15', 11, NULL),
(22, 4, 'item_deactivated', 'Your item "LG 55” 4K UHF smart tv 55UQ8050PSB" has been deactivated by an administrator.', 1, '2025-06-18 16:37:15', 18, NULL),
(23, 1, 'trade_proposal', 'Paul has sent you a trade proposal for iPhone 12', 0, '2025-06-18 17:46:36', 7, 4),
(24, 4, 'item_deactivated', 'Your item "LG 55” 4K UHF smart tv 55UQ8050PSB" has been deactivated by an administrator.', 0, '2025-06-19 01:48:40', 18, NULL);

-- Table: review
DROP TABLE IF EXISTS `review`;
CREATE TABLE `review` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `reviewer_id` int(11) NOT NULL,
  `reviewed_id` int(11) NOT NULL,
  `trade_id` int(11) NOT NULL,
  `rating` int(11) NOT NULL,
  `comment` text DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `reviewer_id` (`reviewer_id`),
  KEY `reviewed_id` (`reviewed_id`),
  KEY `trade_id` (`trade_id`),
  CONSTRAINT `review_ibfk_1` FOREIGN KEY (`reviewer_id`) REFERENCES `user` (`id`),
  CONSTRAINT `review_ibfk_2` FOREIGN KEY (`reviewed_id`) REFERENCES `user` (`id`),
  CONSTRAINT `review_ibfk_3` FOREIGN KEY (`trade_id`) REFERENCES `trade` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: review_photo
DROP TABLE IF EXISTS `review_photo`;
CREATE TABLE `review_photo` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `review_id` int(11) NOT NULL,
  `photo_path` varchar(200) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `review_id` (`review_id`),
  CONSTRAINT `review_photo_ibfk_1` FOREIGN KEY (`review_id`) REFERENCES `review` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: trade
DROP TABLE IF EXISTS `trade`;
CREATE TABLE `trade` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sender_id` int(11) NOT NULL,
  `receiver_id` int(11) NOT NULL,
  `requested_item_id` int(11) NOT NULL,
  `status` varchar(20) DEFAULT NULL,
  `message` text DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `sender_completed` tinyint(1) DEFAULT NULL,
  `receiver_completed` tinyint(1) DEFAULT NULL,
  `sender_completed_at` datetime DEFAULT NULL,
  `receiver_completed_at` datetime DEFAULT NULL,
  `completed_at` datetime DEFAULT NULL,
  `auto_completed` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `sender_id` (`sender_id`),
  KEY `receiver_id` (`receiver_id`),
  KEY `requested_item_id` (`requested_item_id`),
  CONSTRAINT `trade_ibfk_1` FOREIGN KEY (`sender_id`) REFERENCES `user` (`id`),
  CONSTRAINT `trade_ibfk_2` FOREIGN KEY (`receiver_id`) REFERENCES `user` (`id`),
  CONSTRAINT `trade_ibfk_3` FOREIGN KEY (`requested_item_id`) REFERENCES `item` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `trade` (`id`, `sender_id`, `receiver_id`, `requested_item_id`, `status`, `message`, `created_at`, `updated_at`, `sender_completed`, `receiver_completed`, `sender_completed_at`, `receiver_completed_at`, `completed_at`, `auto_completed`) VALUES
(1, 2, 1, 11, 'pending', '', '2025-06-15 07:31:36', '2025-06-17 09:18:10', 0, 0, NULL, NULL, NULL, 0),
(2, 2, 4, 18, 'completed', 'testing', '2025-06-15 07:32:45', '2025-06-17 11:31:33', 1, 0, '2025-06-17 09:22:40', NULL, NULL, 0),
(3, 2, 4, 15, 'pending', 'hi i want to trade with this can?', '2025-06-17 09:06:05', '2025-06-17 11:32:48', 0, 0, NULL, NULL, NULL, 0),
(4, 4, 1, 7, 'pending', '', '2025-06-18 17:46:36', '2025-06-18 17:46:36', 0, 0, NULL, NULL, NULL, 0);

-- Table: trade_item
DROP TABLE IF EXISTS `trade_item`;
CREATE TABLE `trade_item` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `trade_id` int(11) NOT NULL,
  `item_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `trade_id` (`trade_id`),
  KEY `item_id` (`item_id`),
  CONSTRAINT `trade_item_ibfk_1` FOREIGN KEY (`trade_id`) REFERENCES `trade` (`id`),
  CONSTRAINT `trade_item_ibfk_2` FOREIGN KEY (`item_id`) REFERENCES `item` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `trade_item` (`id`, `trade_id`, `item_id`) VALUES
(1, 1, 9),
(2, 2, 10),
(3, 3, 3),
(4, 4, 14),
(5, 4, 15),
(6, 4, 17);

-- Table: user
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(80) NOT NULL,
  `email` varchar(120) NOT NULL,
  `password_hash` varchar(255) DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL,
  `mobile_number` varchar(20) DEFAULT NULL,
  `region` varchar(100) NOT NULL,
  `city` varchar(100) NOT NULL,
  `profile_photo` varchar(255) DEFAULT NULL,
  `is_admin` tinyint(1) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `user` (`id`, `username`, `email`, `password_hash`, `name`, `mobile_number`, `region`, `city`, `profile_photo`, `is_admin`, `is_active`, `created_at`) VALUES
(1, 'Jasmine', 'Jasmine@gmail.com', 'pbkdf2:sha256:600000$7wd4z4pT9T9kn4bz$bcc992465a4703baae6cfb2e76b9957e37fcaef0bd1ea008081ebdf3910d9653', 'Jasmine', NULL, 'Johor', 'Johor Bahru', NULL, 0, 1, '2025-06-15 06:45:51'),
(2, 'Charles', 'Charles@gmail.com', 'pbkdf2:sha256:600000$0lr2auefPbZ3HL72$d56f5c26b181925166fc08947fea5426c2668ef5d598bd00422075024b56aafe', 'Charles', NULL, 'Johor', 'Kluang', NULL, 0, 1, '2025-06-15 06:46:30'),
(3, 'Admin', 'Admin@gmail.com', 'pbkdf2:sha256:600000$HdlRmOl4Ap4lgXdC$4bec0a79175ac90bbcf3c1d56049545216e547423ef571b8f7ca4815c48d368c', 'Admin', NULL, 'Kuala Lumpur', 'Kuala Lumpur', NULL, 1, 1, '2025-06-15 06:49:58'),
(4, 'Paul', 'Paul@gmail.com', 'pbkdf2:sha256:600000$QFEBxBSTDtqZgmBP$08e291b12833cd46cfb321719205b79ff78c3491142b60a8a57f21197c86fd62', 'Paul', '', 'Kedah', 'Alor Setar', '1750152548_sanx_rilakkuma_korilakkuma_lim_1747057149_16ef9b4e_progressive.jpg', 0, 1, '2025-06-15 07:11:01');

SET FOREIGN_KEY_CHECKS = 1;
