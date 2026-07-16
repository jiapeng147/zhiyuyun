-- Migration 034: 商业计费优惠码
-- 增加优惠码主表与兑换记录表，用于订阅订单折扣、使用次数限制和后台运营统计。

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS app_billing_coupon (
  id BIGINT NOT NULL AUTO_INCREMENT,
  code VARCHAR(64) NOT NULL,
  name VARCHAR(100) NOT NULL,
  discount_type VARCHAR(20) NOT NULL DEFAULT 'fixed' COMMENT 'fixed/percent',
  discount_value INT NOT NULL DEFAULT 0 COMMENT 'fixed=分, percent=百分比',
  max_discount_cents INT NOT NULL DEFAULT 0 COMMENT '百分比优惠最高抵扣,0=不限制',
  min_amount_cents INT NOT NULL DEFAULT 0 COMMENT '最低订单原价,0=不限制',
  plan_scope JSON NULL COMMENT '适用套餐代码数组,NULL或空数组=全部套餐',
  max_redemptions INT NOT NULL DEFAULT 0 COMMENT '总可用次数,0=不限制',
  per_user_limit INT NOT NULL DEFAULT 1 COMMENT '单用户最多使用次数,0=不限制',
  redeemed_count INT NOT NULL DEFAULT 0,
  status TINYINT NOT NULL DEFAULT 1 COMMENT '1启用 0停用',
  starts_at DATETIME NULL,
  ends_at DATETIME NULL,
  created_time DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  updated_time DATETIME NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE INDEX uk_app_billing_coupon_code (code),
  INDEX idx_app_billing_coupon_status (status),
  INDEX idx_app_billing_coupon_ends (ends_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订阅优惠码';

CREATE TABLE IF NOT EXISTS app_billing_coupon_redemption (
  id BIGINT NOT NULL AUTO_INCREMENT,
  coupon_id BIGINT NOT NULL,
  coupon_code VARCHAR(64) NOT NULL,
  user_id BIGINT NOT NULL,
  order_id BIGINT NOT NULL,
  discount_cents INT NOT NULL DEFAULT 0,
  created_time DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE INDEX uk_app_billing_coupon_order (order_id),
  INDEX idx_app_billing_coupon_user (coupon_id, user_id),
  INDEX idx_app_billing_coupon_code_user (coupon_code, user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订阅优惠码兑换记录';
