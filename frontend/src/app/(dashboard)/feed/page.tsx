"use client";

import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/lib/auth-store";
import { useLang } from "@/lib/i18n";
import { logoUrl } from "@/lib/dashboard-helpers";
import api from "@/lib/api";
import {
  MessageSquare,
  Loader2,
  Heart,
  MessageCircle,
  Trash2,
  Send,
  TrendingUp,
  TrendingDown,
  ChevronDown,
  ChevronUp,
  Crown,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

// ── Types ──
interface Post {
  id: number;
  user_id: string;
  username: string;
  role: string;
  content: string;
  ticker: string | null;
  created_at: string | null;
  like_count: number;
  liked: boolean;
  comment_count: number;
}

interface Comment {
  id: number;
  user_id: string;
  username: string;
  role: string;
  content: string;
  created_at: string | null;
}

interface TickerData {
  price: number;
  change_pct?: number;
}

// ── Helpers ──
const PRO_ROLES = ["pro", "vip", "admin"];

function timeAgo(iso: string | null): string {
  if (!iso) return "";
  const diff = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
  return `${Math.floor(diff / 86400)}d`;
}

function RoleBadge({ role }: { role: string }) {
  if (role === "admin")
    return (
      <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-md text-[9px] font-black tracking-wider bg-[#FF453A]/15 text-[#FF453A] border border-[#FF453A]/25">
        <ShieldCheck size={9} /> ADMIN
      </span>
    );
  if (role === "vip")
    return (
      <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-md text-[9px] font-black tracking-wider bg-[#FFD700]/15 text-[#FFD700] border border-[#FFD700]/25">
        <Crown size={9} /> VIP
      </span>
    );
  if (role === "pro")
    return (
      <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-md text-[9px] font-black tracking-wider bg-[#D0FD3E]/15 text-[#D0FD3E] border border-[#D0FD3E]/25">
        <Sparkles size={9} /> PRO
      </span>
    );
  return null;
}

// ── Ticker Chip ──
function TickerChip({ ticker }: { ticker: string }) {
  const [data, setData] = useState<TickerData | null>(null);

  useEffect(() => {
    api
      .get<{ ticker: string; price: number }>(`/api/market/price/${ticker}`)
      .then(({ data: d }) => setData({ price: d.price }))
      .catch(() => {});
  }, [ticker]);

  return (
    <div
      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl mt-2 border transition-all hover:brightness-110"
      style={{ background: "var(--input-bg)", borderColor: "var(--border-default)" }}
    >
      <img
        src={logoUrl(ticker)}
        alt=""
        className="w-5 h-5 rounded-full"
        onError={(e) => {
          (e.target as HTMLImageElement).style.display = "none";
        }}
      />
      <span className="font-black text-xs" style={{ color: "var(--text-primary)" }}>
        ${ticker}
      </span>
      {data && (
        <span className="text-xs font-bold tabular-nums" style={{ color: "var(--text-muted)" }}>
          ${data.price.toFixed(2)}
        </span>
      )}
    </div>
  );
}

// ── Comment Section ──
function CommentSection({
  postId,
  commentCount,
  canPost,
}: {
  postId: number;
  commentCount: number;
  canPost: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(false);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [count, setCount] = useState(commentCount);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get<{ comments: Comment[] }>(`/api/feed/${postId}/comments`);
      setComments(data.comments || []);
      setCount(data.comments?.length || 0);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, [postId]);

  const toggle = () => {
    if (!open) load();
    setOpen(!open);
  };

  const submit = async () => {
    if (!text.trim() || sending) return;
    setSending(true);
    try {
      await api.post(`/api/feed/${postId}/comments`, { content: text.trim() });
      setText("");
      load();
    } catch {
      /* ignore */
    } finally {
      setSending(false);
    }
  };

  return (
    <div>
      <button
        onClick={toggle}
        className="flex items-center gap-1.5 text-xs transition-colors"
        style={{ color: "var(--text-muted)" }}
      >
        <MessageCircle size={14} />
        <span className="font-bold tabular-nums">{count}</span>
        {open ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>

      {open && (
        <div className="mt-3 ml-1 pl-3 space-y-2" style={{ borderLeft: "2px solid var(--border-default)" }}>
          {loading ? (
            <Loader2 size={14} className="animate-spin" style={{ color: "var(--text-muted)" }} />
          ) : comments.length === 0 ? (
            <p className="text-xs" style={{ color: "var(--text-dim)" }}>
              No comments yet
            </p>
          ) : (
            comments.map((c) => (
              <div key={c.id} className="flex gap-2">
                <div
                  className="w-6 h-6 rounded-full flex items-center justify-center text-[9px] font-black shrink-0"
                  style={{ background: "var(--input-bg)", color: "var(--text-muted)" }}
                >
                  {c.username.slice(0, 2).toUpperCase()}
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-xs font-bold" style={{ color: "var(--text-primary)" }}>
                      {c.username}
                    </span>
                    <RoleBadge role={c.role} />
                    <span className="text-[10px]" style={{ color: "var(--text-dim)" }}>
                      {timeAgo(c.created_at)}
                    </span>
                  </div>
                  <p className="text-xs mt-0.5" style={{ color: "var(--text-secondary)" }}>
                    {c.content}
                  </p>
                </div>
              </div>
            ))
          )}

          {/* Comment input */}
          {canPost && (
            <div className="flex gap-2 mt-2">
              <input
                type="text"
                placeholder="Write a comment..."
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && submit()}
                maxLength={300}
                className="flex-1 text-xs px-3 py-2 rounded-xl outline-none border transition-colors"
                style={{
                  background: "var(--input-bg)",
                  borderColor: "var(--border-default)",
                  color: "var(--text-primary)",
                }}
              />
              <button
                onClick={submit}
                disabled={!text.trim() || sending}
                className="p-2 rounded-xl transition-all disabled:opacity-30"
                style={{ background: "var(--input-bg)" }}
              >
                {sending ? (
                  <Loader2 size={14} className="animate-spin" style={{ color: "var(--text-muted)" }} />
                ) : (
                  <Send size={14} style={{ color: "#D0FD3E" }} />
                )}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main Page ──
export default function FeedPage() {
  const { lang } = useLang();
  const user = useAuth((s) => s.user);
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  // Compose state
  const [content, setContent] = useState("");
  const [ticker, setTicker] = useState("");
  const [posting, setPosting] = useState(false);

  const role = user?.role?.toLowerCase() || "free";
  const canPost = PRO_ROLES.includes(role);

  const fetchPosts = useCallback(
    async (offset = 0, append = false) => {
      if (!append) setLoading(true);
      else setLoadingMore(true);
      try {
        const { data } = await api.get<{ posts: Post[] }>(`/api/feed?offset=${offset}&limit=20`);
        const newPosts = data.posts || [];
        if (append) {
          setPosts((prev) => [...prev, ...newPosts]);
        } else {
          setPosts(newPosts);
        }
        setHasMore(newPosts.length >= 20);
      } catch {
        /* ignore */
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    []
  );

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  const handlePost = async () => {
    if (!content.trim() || posting) return;
    setPosting(true);
    try {
      await api.post("/api/feed", {
        content: content.trim(),
        ticker: ticker.trim().toUpperCase() || null,
      });
      setContent("");
      setTicker("");
      fetchPosts();
    } catch {
      /* ignore */
    } finally {
      setPosting(false);
    }
  };

  const handleLike = async (postId: number) => {
    try {
      const { data } = await api.post<{ liked: boolean; count: number }>(`/api/feed/${postId}/like`);
      setPosts((prev) =>
        prev.map((p) => (p.id === postId ? { ...p, liked: data.liked, like_count: data.count } : p))
      );
    } catch {
      /* ignore */
    }
  };

  const handleDelete = async (postId: number) => {
    if (!confirm(lang === "TH" ? "ลบโพสต์นี้?" : "Delete this post?")) return;
    try {
      await api.delete(`/api/feed/${postId}`);
      setPosts((prev) => prev.filter((p) => p.id !== postId));
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1
          className="text-2xl font-black tracking-wide flex items-center gap-3"
          style={{ color: "var(--text-primary)" }}
        >
          <MessageSquare className="text-[#AF52DE]" size={24} />
          {lang === "TH" ? "Social Feed" : "Social Feed"}
        </h1>
        <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
          {lang === "TH" ? "แชร์ไอเดียการลงทุน พูดคุยกับชุมชน" : "Share trade ideas & discuss with the community"}
        </p>
      </div>

      {/* ── Compose Box ── */}
      {canPost && (
        <div
          className="border rounded-2xl p-4 mb-6 transition-all"
          style={{ background: "var(--bg-card)", borderColor: "var(--border-default)" }}
        >
          <textarea
            placeholder={lang === "TH" ? "แชร์มุมมองตลาด, ไอเดียเทรด..." : "Share your market view, trade idea..."}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            maxLength={500}
            rows={3}
            className="w-full resize-none text-sm outline-none rounded-xl p-3 border transition-colors"
            style={{
              background: "var(--input-bg)",
              borderColor: "var(--border-default)",
              color: "var(--text-primary)",
            }}
          />
          <div className="flex items-center justify-between mt-3">
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Ticker (optional)"
                value={ticker}
                onChange={(e) => setTicker(e.target.value)}
                maxLength={10}
                className="w-32 text-xs px-3 py-2 rounded-xl outline-none border transition-colors"
                style={{
                  background: "var(--input-bg)",
                  borderColor: "var(--border-default)",
                  color: "var(--text-primary)",
                }}
              />
              <span className="text-[10px] tabular-nums" style={{ color: "var(--text-dim)" }}>
                {content.length}/500
              </span>
            </div>
            <button
              onClick={handlePost}
              disabled={!content.trim() || posting}
              className="flex items-center gap-2 px-5 py-2 rounded-xl font-black text-sm tracking-wider transition-all disabled:opacity-40"
              style={{ background: "#D0FD3E", color: "#080B10" }}
            >
              {posting ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
              {lang === "TH" ? "โพสต์" : "Post"}
            </button>
          </div>
        </div>
      )}

      {/* ── Posts Feed ── */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-[#D0FD3E]" />
        </div>
      ) : posts.length === 0 ? (
        <div
          className="border rounded-2xl p-12 text-center"
          style={{ background: "var(--bg-card)", borderColor: "var(--border-default)" }}
        >
          <MessageSquare className="w-12 h-12 mx-auto mb-4" style={{ color: "var(--text-dim)" }} />
          <p className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>
            {lang === "TH" ? "ยังไม่มีโพสต์" : "No posts yet"}
          </p>
          <p className="text-sm mt-2" style={{ color: "var(--text-muted)" }}>
            {lang === "TH" ? "เป็นคนแรกที่แชร์ไอเดีย!" : "Be the first to share an idea!"}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {posts.map((post) => {
            const isOwner = post.user_id === user?.user_id;
            const isAdmin = role === "admin";
            const canDelete = isOwner || isAdmin;

            return (
              <div
                key={post.id}
                className="border rounded-2xl overflow-hidden transition-all hover:border-white/10"
                style={{ background: "var(--bg-card)", borderColor: "var(--border-default)" }}
              >
                {/* Post header */}
                <div className="px-4 pt-4 pb-2 flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    {/* Avatar */}
                    <div
                      className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-black shrink-0"
                      style={{
                        background:
                          post.role === "admin"
                            ? "rgba(255,69,58,0.15)"
                            : post.role === "pro"
                              ? "rgba(208,253,62,0.1)"
                              : "var(--input-bg)",
                        color:
                          post.role === "admin"
                            ? "#FF453A"
                            : post.role === "pro"
                              ? "#D0FD3E"
                              : "var(--text-muted)",
                      }}
                    >
                      {post.username.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-black text-sm" style={{ color: "var(--text-primary)" }}>
                          {post.username}
                        </span>
                        <RoleBadge role={post.role} />
                      </div>
                      <span className="text-[10px]" style={{ color: "var(--text-dim)" }}>
                        {timeAgo(post.created_at)}
                      </span>
                    </div>
                  </div>

                  {canDelete && (
                    <button
                      onClick={() => handleDelete(post.id)}
                      className="p-1.5 rounded-lg transition-all opacity-0 group-hover:opacity-100 hover:bg-[#FF453A]/10"
                      style={{ color: "var(--text-dim)" }}
                      title="Delete"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>

                {/* Content */}
                <div className="px-4 pb-2">
                  <p
                    className="text-sm leading-relaxed whitespace-pre-wrap"
                    style={{ color: "var(--text-secondary)" }}
                  >
                    {post.content}
                  </p>
                  {post.ticker && <TickerChip ticker={post.ticker} />}
                </div>

                {/* Actions bar */}
                <div
                  className="px-4 py-3 flex items-center gap-5"
                  style={{ borderTop: "1px solid var(--border-subtle)" }}
                >
                  {/* Like */}
                  <button
                    onClick={() => handleLike(post.id)}
                    className="flex items-center gap-1.5 text-xs font-bold transition-all"
                    style={{ color: post.liked ? "#FF453A" : "var(--text-muted)" }}
                  >
                    <Heart
                      size={15}
                      fill={post.liked ? "#FF453A" : "none"}
                      className="transition-transform active:scale-125"
                    />
                    <span className="tabular-nums">{post.like_count}</span>
                  </button>

                  {/* Comments */}
                  <CommentSection postId={post.id} commentCount={post.comment_count} canPost={canPost} />
                </div>
              </div>
            );
          })}

          {/* Load more */}
          {hasMore && (
            <button
              onClick={() => fetchPosts(posts.length, true)}
              disabled={loadingMore}
              className="w-full py-3 rounded-2xl text-sm font-bold transition-all border"
              style={{
                background: "var(--bg-card)",
                borderColor: "var(--border-default)",
                color: "var(--text-muted)",
              }}
            >
              {loadingMore ? (
                <Loader2 size={16} className="animate-spin mx-auto" />
              ) : lang === "TH" ? (
                "โหลดเพิ่มเติม"
              ) : (
                "Load More"
              )}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
