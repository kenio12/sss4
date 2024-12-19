document.addEventListener("DOMContentLoaded", function() {
    var lastScrollTop = 0;
    var header = document.querySelector(".fixed-header");

    window.addEventListener("scroll", function() {
        var currentScroll = window.pageYOffset || document.documentElement.scrollTop;
        
        // 上にスクロールした場合、ヘッダーを表示
        if (currentScroll < lastScrollTop) {
            header.style.top = "0";
        } 
        // 下にスクロールした場合、ヘッダーを非表示
        else if (currentScroll > lastScrollTop) {
            header.style.top = "-100px"; // ヘッダーの高さに合わせて調整してください
        }
        
        // 0以下にならないようにする
        lastScrollTop = currentScroll <= 0 ? 0 : currentScroll;
    }, false);

    var scrollPosition = localStorage.getItem('scrollPosition');
    if (scrollPosition) {
        window.scrollTo(0, parseInt(scrollPosition));
        localStorage.removeItem('scrollPosition');
    }

    // document.querySelectorAll('.pagination a').forEach(link => {
    //     link.onclick = function() {
    //         localStorage.setItem('scrollPosition', window.pageYOffset.toString());
    //     };
    // });

    const likeButtons = document.querySelectorAll('.like-button');
    likeButtons.forEach(function(likeButton) {
        likeButton.addEventListener('click', function(e) {
            e.preventDefault();
            const novelId = this.dataset.novelId;
            const csrftoken = getCookie('csrftoken');
            fetch(`/novels/${novelId}/like/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 'novel_id': novelId }),
            })
            .then(response => response.json())
            .then(data => {
                const likeIcon = this.querySelector('.like-icon');
                likeIcon.src = data.is_liked ? this.dataset.likeImg : this.dataset.unlikeImg;
                const likeCount = this.nextElementSibling;
                likeCount.textContent = data.likes_count;
            })
            .catch(error => console.error('Error:', error));

            const likeIcon = this.querySelector('.like-icon');
            likeIcon.classList.add('rotate-effect');

            const sparkle = document.createElement('span');
            sparkle.classList.add('sparkle-effect');
            sparkle.textContent = '✨';
            this.appendChild(sparkle);

            sparkle.addEventListener('animationend', function() {
                sparkle.remove();
            });

            likeIcon.addEventListener('animationend', function() {
                likeIcon.classList.remove('rotate-effect');
            });
        });
    });

    const userNickname = document.getElementById('user-nickname');
    const dropdownMenu = document.getElementById('dropdown-menu');
    if (userNickname && dropdownMenu) {
        userNickname.addEventListener('click', function(event) {
            console.log("ニックネームがクリックされました。"); // この行を追加
            event.preventDefault();
            dropdownMenu.style.display = dropdownMenu.style.display === "none" || !dropdownMenu.style.display ? "block" : "none";
        });
    }

    function logout() {
        fetch(logoutUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
            credentials: 'same-origin'
        }).then(response => {
            if (response.ok) {
                window.location.reload();
            } else {
                alert('ログアウトに失敗しました。');
            }
        });
    }

    const logoutLink = document.getElementById('logout-link');
    if (logoutLink) {
        logoutLink.addEventListener('click', function(event) {
            event.preventDefault();
            logout();
        });
    }

    // 以下ヘッダーをスクロールで出したり引っ込めたりの部分
    // ヘッダーの高さを設定する関数
    function setHeaderHeight() {
        var headerHeight = document.querySelector(".fixed-header").offsetHeight;
        document.querySelector(".main-content").style.paddingTop = headerHeight + "px";
    }

    // 初期ロード時にヘッダーの高さを設定
    setHeaderHeight();

    // ウィンドウのサイズが変更された時にヘッダーの高さを再設定
    window.addEventListener('resize', setHeaderHeight);

    // ヘッダーの高さに基づいてメインコンテンツのpadding-topを設定
    var headerHeight = document.querySelector(".fixed-header").offsetHeight;
    document.querySelector(".main-content").style.paddingTop = headerHeight + "px";

// コメントの既読・未読を切り替えるボタンにイベントリスナーを追加
document.querySelectorAll('.toggle-read-status').forEach(function(checkbox) {
    checkbox.addEventListener('change', function() {
        console.log('Dataset:', this.dataset); // datasetの内容を確認
        const commentId = this.dataset.commentId;
        const novelId = this.dataset.novelId; // 小説のIDを取得
        console.log('Novel ID:', novelId); // novelIdの値を確認
        const isRead = this.checked;

        // toggleReadStatus 関数を呼び出して、コメントの既読状態を切り替える
        toggleReadStatus(commentId, isRead, novelId);
    });
});

// ページ読み込み時と定期的に未読コメント数を更新
// updateUnreadCommentsCount();
// setInterval(updateUnreadCommentsCount, 60000); // 1分ごとに更新


    // タイトルの文字数を更新する関数
    function updateTitleWordCount() {
        const titleField = document.querySelector('.title');
        const titleWordCountDisplay = document.getElementById('titleWordCount');
        if (titleField && titleWordCountDisplay) {
            const titleWordCount = titleField.value.length;
            titleWordCountDisplay.textContent = `${titleWordCount} / 30文字`;
        }
    }

    // タイトル入力フィールドにイベントリスナーを追加
    const titleField = document.querySelector('.title');
    if (titleField) {
        titleField.addEventListener('input', updateTitleWordCount);
        updateTitleWordCount(); // ページ読み込み時にタイトルの文字数を更新
    }

    // 小説の内容入力フィールドを取得し、以前の宣言を削除またはコメントアウト
    const contentInput = document.querySelector('.content'); // この行は残す




    // 文字数を表示する要素を取得
    const wordCountDisplay = document.getElementById('wordCount');

    // フッターの文字数カウンターを表示する要素を取得
    const footerWordCountDisplay = document.getElementById('footerWordCount');

    // 文字数を更新する関数
    function updateFooterWordCount() {
        if (contentInput && footerWordCountDisplay) {
            const count = contentInput.value.length;
            const formattedCount = count.toLocaleString();
            const formattedMax = (10000).toLocaleString(); // 最大文字数もフォーマット
            footerWordCountDisplay.textContent = `${formattedCount} / ${formattedMax}文字`;
        }
    }

    // コンテンツ入力フィールドに 'click' と 'input' イベントリスナーを追加
    if (contentInput) {
        // コンテンツ入力フィールドに 'click' と 'input' イベントリスナーを追加
        contentInput.addEventListener('click', updateFooterWordCount);
        contentInput.addEventListener('input', updateFooterWordCount);
    }
    
// テキストエリアの高さを計算して、高さ８５％のテキストエリアにする。
const contentTextarea = document.querySelector('.content');
if (contentTextarea) {
    function setInitialTextareaHeight() {
        // 画面の縦幅から、テキストエリア以外の要素の高さを引いた値をテキストエリアの高さとする
        // ここでは例として、画面の100%の高さをテキストエリアに設定しています
        const screenHeight = window.innerHeight;
        const otherElementsHeight = 100; // ヘッダー、フッター、マージンなどの高さの合計を推定
        const textareaHeight = screenHeight - otherElementsHeight; // 画面の100%からその他要素の高さを引く
        contentTextarea.style.height = `${textareaHeight}px`;
    }

    // ページ読み込み時に一度だけテキストエリアの高さを設定
    setInitialTextareaHeight();
}

    // ログアウトアイコンのクリックイベントを処理
    const logoutIcon = document.getElementById('logout-icon');
    if (logoutIcon) {
        logoutIcon.addEventListener('click', function(event) {
            event.preventDefault(); // デフォルトのアンカー動作をキャンセル
            const logoutConfirmed = confirm("ログアウトするっすか？");
            if (logoutConfirmed) {
                // ログアウト処理を実行
                logout(); // 既に定義されているlogout関数を呼び出す
            }
        });
    }

    // コメントテキストエリアの文字数カウントと警告メッセージの表示
    const commentTextarea = document.querySelector('.comment-textarea');
    if (commentTextarea) { // コメントテキストエリアが存在する場合のみ実行
        const feedback = document.createElement('div');
        feedback.id = 'comment-feedback';
        commentTextarea.parentNode.insertBefore(feedback, commentTextarea.nextSibling);

        commentTextarea.addEventListener('input', function () {
            const remaining = 1000 - this.value.length;
            if (remaining < 0) {
                feedback.innerHTML = '<span style="color: red;">コメントは1000文字までです！</span>';
            } else {
                feedback.innerHTML = '残り ' + remaining + ' 文字';
            }
        });
    }

    // 未読コメントのデータを取得する関数
    // function fetchUnreadComments() {
    //     fetch('/novels/api/unread-comments/') // 未読コメントのAPIエンドポイント
    //         .then(response => response.json())
    //         .then(data => {
    //             createUnreadCommentsElements(data.unread_comments);
    //         })
    //         .catch(error => console.error('Error:', error));
    // }

// 未読コメントのHTML要素を生成する関数
// function createUnreadCommentsElements(unreadComments) {
//     const notificationsContainer = document.getElementById('notifications-container');
//     if (!notificationsContainer) {
//         console.error('Notifications container not found.');
//         return; // notificationsContainerがnullの場合、ここで処理を中断
//     }
//     const colors = ['red', 'blue', 'orange', 'purple', 'green', 'black']; // 背景色のリスト
//     let colorIndex = 0;

//     unreadComments.forEach(comment => {
//         const countElement = document.createElement('div');
//         countElement.className = `unread-comments-count ${colors[colorIndex]}`;
//         countElement.textContent = comment.count;
//         notificationsContainer.appendChild(countElement); // コンテナに追加

//         // 次の色に更新
//         colorIndex = (colorIndex + 1) % colors.length;
//     });
// }


// post+edit画面内のメッセージ非表示関連
// メッセージの表示/非表示を切り替える共通の関数
function toggleMessageVisibility(messageId, storageKey) {
    const messageShown = localStorage.getItem(storageKey);
    const messageElement = document.getElementById(messageId);

    // messageElement が null でないことを確認
    if (messageElement) {
        // メッセージがまだ表示されていない場合は、メッセージを表示する
        if (messageShown !== 'true') {
            messageElement.style.display = 'block';
        }

        // メッセージの非表示ボタンクリックイベントを設定
        const button = messageElement.querySelector('.toggle-message-button');
        if (button) {
            button.addEventListener('click', function() {
                // 確認ダイアログを表示
                const confirmHide = confirm("このメッセージを非表示にしますか？");
                if (confirmHide) {
                    // ユーザーが「はい」を選択した場合、メッセージを非表示にする
                    messageElement.style.display = 'none';
                    localStorage.setItem(storageKey, 'true');
                }
            });
        }
    } else {
        // messageElement が null の場合、警告をログに出力
        console.warn(`Element with ID ${messageId} not found.`);
    }
}


});





function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

    document.querySelectorAll('.comment').forEach(function(comment) {
        const content = comment.querySelector('.comment-content');
        // コメントの高さを取得するために一時的に展開する
        content.style.maxHeight = 'none';
        const contentHeight = content.offsetHeight;
        // コメントの内容が折りたたみ表示に収まる場合は、maxHeightを設定
        content.style.maxHeight = contentHeight > 80 ? '' : contentHeight + 'px';

        // コメントの内容が特定の高さを超えている場合のみボタンを追加
        if (contentHeight > 80) { // 80px = 5行分の高さ（おおよその値）
            const button = document.createElement('button');
            button.textContent = 'もっと見る';
            button.classList.add('toggle-button');
            comment.appendChild(button);

            button.addEventListener('click', function() {
                if (content.classList.contains('expanded')) {
                    content.classList.remove('expanded');
                    button.classList.remove('expanded');
                    button.textContent = 'もっと見る'; // ボタンのテキストを「もっと見る」に変更
                } else {
                    content.classList.add('expanded');
                    button.classList.add('expanded');
                    button.textContent = '縮める'; // ボタンのテキストを「縮める」に変更
                }
            });
        }
    });

// コメントの既読状態を切り替える関数
function toggleReadStatus(commentId, isRead, novelId) {
    fetch(`/novels/toggle-comment-read/${commentId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_read: isRead }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 未読コメント数の更新は1回だけ
            updateUnreadCommentsCount(novelId);
        } else {
            console.error('コメントの状態を更新できませんでした。');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// 小説のIDを引数として受け取るように変更
function checkForOtherUnreadComments(novelId) {
    // novelIdの値をコンソールに出力
    console.log(`わいやあnovelId: ${novelId}`);

    // URLに小説のIDを含める
    fetch(`/novels/check-unread-comments/${novelId}/`)
    .then(response => response.json())
    .then(data => {
        if (data.unread_novel_id) {
            // 未読コメントがある小説の詳細ページに遷移
            window.location.href = `/novels/${data.unread_novel_id}/`;
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}


// 統合された未読コメント数を更新する関数
function updateUnreadCommentsCount(novelId, newCount = null) {
    console.log('novelId:', novelId); // デバッグ用のログを追加
    if (!novelId) {
        console.error('novelId is undefined.');
        return; // novelIdがundefinedの場合は、ここで処理を中断
    }

    const endpoint = `/novels/unread-comments-count/${novelId}/`;
    return fetch(endpoint)
        .then(response => response.json())
        .then(data => {
            const count = newCount !== null ? newCount : data.unread_comments_count;
            const unreadCommentsCountElement = document.getElementById(`unread-comments-count-novel-${novelId}`);
            const commentIconContainer = document.querySelector(`.comment-icon-container[data-novel-id="${novelId}"]`);

            if (unreadCommentsCountElement) {
                unreadCommentsCountElement.textContent = count;
                if (count > 0) {
                    unreadCommentsCountElement.style.display = 'block';
                    if (commentIconContainer) {
                        commentIconContainer.style.display = 'inline-block'; // コンテナを表示
                        commentIconContainer.style.backgroundImage = "url('/static/images/comments-icon.svg')"; // 未読アイコンを表示
                    }
                } else {
                    unreadCommentsCountElement.style.display = 'none';
                    if (commentIconContainer) {
                        commentIconContainer.style.display = 'none'; // コンテナを非表示
                    }
                }
            } else {
                console.error(`Element for unread comments count of novel ${novelId} not found.`);
            }
        })
        .catch(error => console.error('Error:', error));
}

// let nextPage = 2;  // 次に読み込むページ番号（初期値は2）
// let isLoading = false;  // データ読み込み中かどうかのフラグ

// // スクロールイベントリスナーを変数に格納
// const handleScroll = () => {
//     const documentHeight = document.body.scrollHeight;
//     const currentScroll = window.innerHeight + window.scrollY;
//     if (currentScroll >= documentHeight - 100 && !isLoading) {
//         isLoading = true;  // データ読み込み中に設定
//         fetch(`/novels/?page=${nextPage}`, {
//             headers: {
//                 'X-Requested-With': 'XMLHttpRequest'
//             }
//         })
//         .then(response => response.json())
//         .then(data => {
//             if (data.has_next) {
//                 nextPage++;  // 次のページ番号を更新
//             } else {
//                 // これ以上読み込むページがない場合は、イベントリスナーを削除
//                 window.removeEventListener('scroll', handleScroll, { passive: true });
//             }
//             isLoading = false;  // データ読み込み完了
//             const tbody = document.querySelector('.novels-list-container table tbody');
//             if (tbody) { // tbodyがnullでないことを確認
//                 data.novels.forEach(novel => {
//                     const tr = document.createElement('tr');
//                     tr.classList.add('fade-in'); // 初期状態でfade-inクラスを追加
//                     tr.innerHTML = `
//                         <td><span class="full-cell-link">${novel.word_count}</span></td>
//                         <td>
//                             <a class="full-cell-link" href="/novels/${novel.id}/" style="display: block; text-decoration: none; height: 100%; width: 100%;">
//                                 ${novel.title}
//                             </a>
//                         </td>
//                         <td>
//                             <a class="full-cell-link" href="/accounts/profile/${novel.author_id}/" style="display: block; text-decoration: none; height: 100%; width: 100%;">
//                                 ${novel.author_nickname}
//                             </a>
//                         </td>
//                         <td><span class="full-cell-link">${novel.published_date}</span></td>
//                     `;
//                     // tr要素に対する処理
//                     tbody.appendChild(tr);
//                     // 少し遅延させてからvisibleクラスを追加する
//                     setTimeout(() => tr.classList.add('visible'), 200);
//                 });
//             } else {
//                 console.error('tbodyが見つかりません。');
//             }
//         })
//         .catch(error => {
//             console.error('Error:', error);
//             isLoading = false;
//         });
//     }
// };

// // スクロールイベントリスナーを登録
// window.addEventListener('scroll', handleScroll, { passive: true });






// 小説詳細のコメント一覧も遅延
document.addEventListener('DOMContentLoaded', function () {
    const commentsContainer = document.querySelector('.comments-container');
    if (!commentsContainer) return;

    commentsContainer.addEventListener('scroll', function() {
        // コメントコンテナのスクロール位置を取得
        const scrollPosition = commentsContainer.scrollTop + commentsContainer.clientHeight;
        // コメントコンテナの全体の高さ
        const totalHeight = commentsContainer.scrollHeight;

        // スクロールが下端に近づいたら新しいコメントを読み込む
        if (scrollPosition >= totalHeight - 100 && !isLoading) {
            isLoading = true;
            fetch(`/novels/${novelId}/load_more_comments?page=${nextPage}`)
                .then(response => response.json())
                .then(data => {
                    if (data.has_next) {
                        nextPage++;
                        displayComments(data); // コメントを表示する処理を呼び出し
                        // コメントを表示する処理をここに書く
                    } else {
                        // これ以上読み込むページがない場合は、イベントリスナーを削除
                        commentsContainer.removeEventListener('scroll', handleScroll);
                    }
                    isLoading = false;
                })
                .catch(error => {
                    console.error('Error:', error);
                    isLoading = false;
                });
        }
    });
});

// 遅延のコメントを表示する処理
function displayComments(data) {
    const commentsList = document.querySelector('.comments-list');
    if (!commentsList) return;

    data.comments.forEach(comment => {
        const commentElement = document.createElement('div');
        commentElement.classList.add('comment');
        commentElement.innerHTML = `
            <p class="comment-author"><strong>${comment.author__nickname}</strong> - ${new Date(comment.created_at).toLocaleString()}</p>
            <p class="comment-content">${comment.content}</p>
        `;
        commentsList.appendChild(commentElement);
    });
}